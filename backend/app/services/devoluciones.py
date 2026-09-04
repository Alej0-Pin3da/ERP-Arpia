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
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.ventas import Devolucion, DevolucionItem, DocumentState, Venta
from app.services.inventory import explosion_materiales, reponer_stock


def registrar_devolucion(db: Session, user_id: int | None, payload: dict) -> Devolucion:
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
    if venta.estado == DocumentState.CANCELLED.value:
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
        venta.transition_to(DocumentState.CANCELLED)
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
            raise HTTPException(status_code=400, detail="Debe incluir al menos un item a devolver")
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
        raise HTTPException(status_code=400, detail="tipo debe ser 'total' o 'parcial'")

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
        ) from None
    except Exception:
        db.rollback()
        raise


def actualizar_devolucion(
    db: Session,
    devolucion_id: int,
    motivo=None,
    estado: str | None = None,
    reversed_by: int | None = None,
) -> Devolucion:
    """Edit motivo and/or transition estado of a devolucion.

    - reversed is terminal and immutable (422).
    - motivo can be corrected on draft/confirmed/cancelled.
    - estado (when given) must be a valid DocumentState transition from the
      current state (400 otherwise; reversal requires motivo).
    Single commit; nothing persisted on error.
    """
    devolucion = db.get(Devolucion, devolucion_id)
    if devolucion is None:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    if devolucion.estado == DocumentState.REVERSED.value:
        raise HTTPException(
            status_code=422, detail="Una devolución revertida es inmutable"
        )
    if motivo is not None:
        devolucion.motivo = motivo
    if estado is not None:
        try:
            new_state = DocumentState(estado)
            devolucion.transition_to(
                new_state,
                motivo=motivo,
                reversed_by=reversed_by if new_state == DocumentState.REVERSED else None,
            )
        except ValueError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        db.commit()
        db.refresh(devolucion)
        return devolucion
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto al actualizar la devolución; no se persistió nada",
        ) from None
    except Exception:
        db.rollback()
        raise


def eliminar_devolucion(db: Session, devolucion_id: int) -> None:
    """Hard-delete a devolucion ONLY in draft state.

    Non-draft returns already restored stock (and a 'total' return anulled
    the sale), so hard-deleting them would leave inventory/venta
    inconsistent — use the state transition (cancelled/reversed) instead
    (400 with that hint). Draft deletes remove line items first (ORM-level,
    DB cascade is the backstop) in a single commit.
    """
    devolucion = db.get(Devolucion, devolucion_id)
    if devolucion is None:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    if devolucion.estado != DocumentState.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail=(
                "Solo se puede eliminar una devolución en borrador; "
                "usá la transición de estado (cancelled/reversed) para anularla"
            ),
        )
    try:
        for item in list(devolucion.items):
            db.delete(item)
        db.delete(devolucion)
        db.commit()
    except Exception:
        db.rollback()
        raise


def listar_devoluciones(
    db: Session,
    venta_id: int | None = None,
    fecha_desde=None,
    fecha_hasta=None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Devolucion], int]:
    """List returns ordered by id, with their line items and Venta reference,
    optionally filtered by venta_id, a fecha range (DEV-4) and a global q on
    the motivo. Returns ``(rows, total)`` where total counts the filtered set
    (limit/offset ignored) — the {items, total} contract (API-1)."""
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
    if q is not None:
        stmt = stmt.where(Devolucion.motivo.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = list(db.scalars(stmt.limit(limit).offset(offset)))
    return rows, total
