"""Devoluciones engine — full-cancel and partial-return business logic.

``registrar_devolucion`` runs the whole return (metadata + line items +
inventory restore) inside ONE transaction: the Venta row is locked with
SELECT ... FOR UPDATE so concurrent returns of the same sale serialize and the
second one rejects with 409 (single-return invariant). Refunds always come from
the sale-time ``precio_unitario_aplicado`` snapshot, never from current values.
The caller owns nothing else — this service performs the single commit.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.ventas import Devolucion, DevolucionItem, Venta
from app.services.inventory import explosion_materiales, reponer_stock


def registrar_devolucion(
    db: Session, user_id: int | None, payload: dict
) -> Devolucion:
    """Register a return (full cancel or partial by line), atomically.

    Payload mirrors the future schema fields: ``venta_id``, ``tipo``
    ('total'|'parcial'), ``motivo`` (optional) and ``items`` (optional for
    'total'; required for 'parcial' — a list of ``{producto_id, variante_id,
    cantidad}``).

    - 'total': refund = the full ``Venta.total_venta``, every consumed BOM
      insumo is restored, and the sale becomes 'anulada'.
    - 'parcial': each requested line is validated against the sold quantity
      (422 if it exceeds), priced at the sale-time snapshot, and only the
      returned items' BOM is restored; the sale stays 'completada'.
    - 400 when the sale is already 'anulada' or a total cancel finds no
      material PObs; 409 when the sale already has a return; 409 on any
      constraint failure (nothing persisted).
    """
    venta_id = payload["venta_id"]
    tipo = payload.get("tipo", "parcial")
    motivo = payload.get("motivo")
    items_payload = payload.get("items") or []

    venta = db.get(Venta, venta_id, with_for_update=True)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    if venta.estado == "anulada":
        raise HTTPException(
            status_code=400, detail="La venta ya está anulada; no se puede devolver"
        )

    existente = db.scalar(select(Devolucion).where(Devolucion.venta_id == venta_id))
    if existente is not None:
        raise HTTPException(
            status_code=409,
            detail="La venta ya tiene una devolución registrada",
        )

    explosiones: dict[int, Decimal] = {}

    if tipo == "total":
        for detalle in venta.detalles:
            for insumo_id, qty in explosion_materiales(
                db, detalle.producto_id, detalle.variante_id, detalle.cantidad
            ).items():
                explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty
        if not explosiones:
            raise HTTPException(
                status_code=400,
                detail="La venta no tiene materiales consumibles; no se puede anular",
            )
        venta.estado = "anulada"
        devolucion = Devolucion(
            venta_id=venta_id,
            tipo="total",
            monto_reembolsado=venta.total_venta,
            motivo=motivo,
            usuario_id=user_id,
        )
        db.add(devolucion)
    elif tipo == "parcial":
        # Sold quantities + snapshot unit prices grouped by (producto, variante).
        vendido: dict[tuple[int, int | None], Decimal] = {}
        precios: dict[tuple[int, int | None], Decimal] = {}
        for detalle in venta.detalles:
            key = (detalle.producto_id, detalle.variante_id)
            vendido[key] = vendido.get(key, Decimal("0")) + detalle.cantidad
            precios.setdefault(key, detalle.precio_unitario_aplicado)

        items: list[DevolucionItem] = []
        reembolso = Decimal("0")
        for item in items_payload:
            producto_id = item["producto_id"]
            variante_id = item.get("variante_id")
            cantidad = Decimal(item["cantidad"])
            if cantidad <= 0:
                raise HTTPException(
                    status_code=422, detail="La cantidad devuelta debe ser positiva"
                )
            key = (producto_id, variante_id)
            vendida = vendido.get(key, Decimal("0"))
            if cantidad > vendida:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Cantidad devuelta {cantidad} excede lo vendido "
                        f"{vendida} para el producto {producto_id}"
                    ),
                )
            precio = precios.get(key)
            if precio is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"El producto {producto_id} no pertenece a esta venta",
                )
            subtotal = cantidad * precio
            reembolso += subtotal
            items.append(
                DevolucionItem(
                    producto_id=producto_id,
                    variante_id=variante_id,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal,
                )
            )
            for insumo_id, qty in explosion_materiales(
                db, producto_id, variante_id, cantidad
            ).items():
                explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty

        if not items:
            raise HTTPException(
                status_code=400, detail="Debe incluir al menos un item a devolver"
            )
        devolucion = Devolucion(
            venta_id=venta_id,
            tipo="parcial",
            monto_reembolsado=reembolso,
            motivo=motivo,
            usuario_id=user_id,
            items=items,
        )
        db.add(devolucion)
    else:
        raise HTTPException(
            status_code=400, detail="tipo debe ser 'total' o 'parcial'"
        )

    reponer_stock(db, explosiones)

    try:
        db.commit()
        db.refresh(devolucion)
        return devolucion
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto al registrar la devolución; no se persistió nada",
        )
    except Exception:
        db.rollback()
        raise


def listar_devoluciones(
    db: Session,
    venta_id: int | None = None,
    fecha_desde=None,
    fecha_hasta=None,
    limit: int = 100,
    offset: int = 0,
) -> list[Devolucion]:
    """List returns ordered by id, with their line items and Venta reference,
    optionally filtered by venta_id and a fecha range (DEV-4)."""
    stmt = (
        select(Devolucion)
        .options(
            selectinload(Devolucion.items),
            selectinload(Devolucion.venta),
        )
        .order_by(Devolucion.id)
    )
    if venta_id is not None:
        stmt = stmt.where(Devolucion.venta_id == venta_id)
    if fecha_desde is not None:
        stmt = stmt.where(Devolucion.fecha >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(Devolucion.fecha <= fecha_hasta)
    return list(db.scalars(stmt.limit(limit).offset(offset)))
