"""Inventory engine — flat material explosion, stock-out and sale registration.

Read-only, reusable flat BOM explosion for stock math (shared later by
devoluciones and reportes), FOR-UPDATE stock deduction, and a single-commit
sale registration. Money/quantities stay NUMERIC(15,4); rounding to 2 happens
only at display time.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.clientes import Cliente
from app.models.insumos import Insumo
from app.models.productos import BomInsumo, BomProducto, Producto, VarianteProducto
from app.models.ventas import DetalleVenta, Venta
from app.services.costos import _lineas_insumo_efectivas, calcular_costo_produccion


def explosion_materiales(
    db: Session, producto_id: int, variante_id: int | None, cantidad: Decimal
) -> dict[int, Decimal]:
    """Flat recursive material explosion -> {insumo_id: effective_qty}.

    A product sold in a required quantity (`cantidad`) needs that many raw
    insumos: each direct insumo line contributes `cantidad * qty * (1+waste)`
    and every child combo is flattened recursively into its own insumos (never
    kept as the child product itself). Variant effective lines reuse
    `_lineas_insumo_efectivas` (override-not-sum). A BOM cycle aborts with 409.
    Read-only: issues no locks and no commits, so it is safe to call inside a
    SELECT ... FOR UPDATE transaction.
    """
    cantidad = Decimal(cantidad)
    res: dict[int, Decimal] = {}
    _explode(db, producto_id, variante_id, cantidad, path=[], result=res, root=True)
    return res


def _explode(
    db: Session,
    producto_id: int,
    variante_id: int | None,
    multiplicador: Decimal,
    path: list[int],
    result: dict[int, Decimal],
    root: bool = False,
) -> None:
    if producto_id in path:
        cadena = " -> ".join(str(p) for p in [*path, producto_id])
        raise HTTPException(
            status_code=409, detail=f"Cycle detected in BOM explosion: {cadena}"
        )
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    if root and variante_id is None and producto.variantes:
        raise HTTPException(
            status_code=400,
            detail="El producto tiene variantes; debe indicar variante_id",
        )

    insumo_rows = list(
        db.scalars(
            select(BomInsumo)
            .where(BomInsumo.producto_id == producto_id)
            .order_by(BomInsumo.id)
        )
    )
    producto_rows = list(
        db.scalars(
            select(BomProducto)
            .where(BomProducto.combo_id == producto_id)
            .order_by(BomProducto.id)
        )
    )

    path.append(producto_id)
    try:
        for linea in _lineas_insumo_efectivas(insumo_rows, variante_id):
            cantidad_efectiva = linea.cantidad_requerida * (
                Decimal("1") + linea.porcentaje_desperdicio / Decimal("100")
            )
            contribucion = multiplicador * cantidad_efectiva
            result[linea.insumo_id] = (
                result.get(linea.insumo_id, Decimal("0")) + contribucion
            )
        for linea in producto_rows:
            _explode(
                db,
                linea.producto_incluido_id,
                variante_id,
                multiplicador * linea.cantidad,
                path,
                result,
            )
    finally:
        path.pop()


def descontar_stock(db: Session, explosiones: dict[int, Decimal]) -> None:
    """Subtract an explosion's insumos from stock, atomically.

    Locks every affected Insumo with SELECT ... FOR UPDATE (in id order to
    avoid deadlocks between concurrent sales), verifies enough stock for EVERY
    id, then subtracts only when all checks pass. Insufficient stock raises 409
    and nothing is subtracted (the caller owns the rollback — no commit here).
    """
    for insumo_id in sorted(explosiones):
        cantidad = explosiones[insumo_id]
        # populate_existing is REQUIRED: the insumo may already be loaded in this
        # session's identity map (e.g. via the cost engine's selectin traversal);
        # the FOR UPDATE re-read must overwrite it with the latest committed row,
        # or a concurrent sale would keep seeing stale stock and double-deduct.
        insumo = db.get(
            Insumo, insumo_id, with_for_update=True, populate_existing=True
        )
        if insumo is None:
            raise HTTPException(status_code=404, detail="Insumo not found")
        if insumo.stock_actual < cantidad:
            raise HTTPException(
                status_code=409,
                detail=f"Stock insuficiente para insumo {insumo.nombre!r}",
            )
        insumo.stock_actual -= cantidad


def registrar_venta(db: Session, payload: dict) -> Venta:
    """Register a sale and deduct stock in ONE atomic commit.

    Payload is a plain dict mirroring the future VentaCreate schema field names
    (so a pydantic schema can be passed via ``.model_dump()`` by the routes):
    ``cliente_id``, ``canal_venta``, ``descuento_porcentaje`` and ``detalles``
    (a list of ``{producto_id, variante_id, cantidad, precio_unitario}``).

    Per line it snapshots ``costo_unitario_aplicado`` = the product's current
    production cost (read from ``Insumo.costo_promedio_actual`` through the
    reusable cost engine), aggregates the flat explosion across lines, deducts
    stock with FOR UPDATE (409 if insufficient, all-or-nothing), then commits
    exactly once. ANY failure raises and rolls back — nothing is persisted.
    """
    detalles = payload["detalles"]
    if not detalles:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un detalle")

    cliente_id = payload.get("cliente_id")
    if cliente_id is not None:
        if db.get(Cliente, cliente_id) is None:
            raise HTTPException(status_code=404, detail="Cliente not found")

    canal_venta = payload.get("canal_venta", "feria")
    descuento = Decimal(payload.get("descuento_porcentaje", "0"))
    descuento_factor = Decimal("1") - descuento / Decimal("100")

    explosiones: dict[int, Decimal] = {}
    lineas_costo: list[Decimal] = []
    lineas_subtotal: list[Decimal] = []

    for detalle in detalles:
        producto_id = detalle["producto_id"]
        variante_id = detalle.get("variante_id")
        cantidad = Decimal(detalle["cantidad"])
        precio_unitario = Decimal(detalle["precio_unitario"])

        producto = db.get(Producto, producto_id)
        if producto is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if variante_id is not None:
            variante = db.get(VarianteProducto, variante_id)
            if variante is None or variante.producto_id != producto_id:
                raise HTTPException(
                    status_code=400, detail="variante_id no pertenece al producto"
                )

        costo_unitario = calcular_costo_produccion(db, producto_id, variante_id)
        lineas_costo.append(costo_unitario)
        lineas_subtotal.append(cantidad * precio_unitario)

        for insumo_id, qty in explosion_materiales(
            db, producto_id, variante_id, cantidad
        ).items():
            explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty

    descontar_stock(db, explosiones)

    total_venta = Decimal(sum(lineas_subtotal)) * descuento_factor
    venta = Venta(
        cliente_id=cliente_id,
        canal_venta=canal_venta,
        descuento_porcentaje=descuento,
        total_venta=total_venta,
    )
    db.add(venta)
    for i, detalle in enumerate(detalles):
        db.add(
            DetalleVenta(
                venta=venta,
                producto_id=detalle["producto_id"],
                variante_id=detalle.get("variante_id"),
                cantidad=Decimal(detalle["cantidad"]),
                precio_unitario_aplicado=Decimal(detalle["precio_unitario"]),
                costo_unitario_aplicado=lineas_costo[i],
            )
        )

    try:
        db.commit()
        db.refresh(venta)
        return venta
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto al registrar la venta; no se persistió nada",
        )
    except Exception:
        db.rollback()
        raise