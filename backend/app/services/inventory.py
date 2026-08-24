"""Inventory engine — flat material explosion, stock-out and sale registration.

Read-only, reusable flat BOM explosion for stock math (shared later by
devoluciones and reportes), FOR-UPDATE stock deduction, and a single-commit
sale registration. Money/quantities stay NUMERIC(15,4); rounding to 2 happens
only at display time.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BomCycleDetectedError,
    DomainValidationError,
    EntityNotFoundError,
    InsufficientStockError,
)
from app.models.clientes import Cliente
from app.models.insumos import Insumo
from app.models.productos import BomInsumo, BomProducto, Producto, VarianteProducto
from app.models.ventas import DetalleVenta, DocumentState, Venta
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
        raise BomCycleDetectedError([*path, producto_id])
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise EntityNotFoundError("Producto", producto_id)
    if root and variante_id is None and producto.variantes:
        raise DomainValidationError("El producto tiene variantes; debe indicar variante_id")

    insumo_rows = list(
        db.scalars(
            select(BomInsumo).where(BomInsumo.producto_id == producto_id).order_by(BomInsumo.id)
        )
    )
    producto_rows = list(
        db.scalars(
            select(BomProducto).where(BomProducto.combo_id == producto_id).order_by(BomProducto.id)
        )
    )

    path.append(producto_id)
    try:
        for linea in _lineas_insumo_efectivas(insumo_rows, variante_id):
            cantidad_efectiva = linea.cantidad_requerida * (
                Decimal("1") + linea.porcentaje_desperdicio / Decimal("100")
            )
            contribucion = multiplicador * cantidad_efectiva
            result[linea.insumo_id] = result.get(linea.insumo_id, Decimal("0")) + contribucion
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
        insumo = db.get(Insumo, insumo_id, with_for_update=True, populate_existing=True)
        if insumo is None:
            raise EntityNotFoundError("Insumo", insumo_id)
        if insumo.stock_actual < cantidad:
            raise InsufficientStockError(insumo.nombre)
        insumo.stock_actual -= cantidad


def reponer_stock(db: Session, explosiones: dict[int, Decimal]) -> None:
    """Restore an explosion's insumos back into stock (inverse restock).

    Mirrors ``descontar_stock`` with the sign inverted: locks every affected
    Insumo with SELECT ... FOR UPDATE in id order (deadlock-safe), re-reads the
    latest committed row via ``populate_existing`` so concurrent restocks of the
    same insumo never overwrite each other, and adds the quantity. An unknown
    insumo raises 404. No commit here — the caller owns the transaction.
    """
    for insumo_id in sorted(explosiones):
        insumo = db.get(Insumo, insumo_id, with_for_update=True, populate_existing=True)
        if insumo is None:
            raise EntityNotFoundError("Insumo", insumo_id)
        insumo.stock_actual += explosiones[insumo_id]


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
        raise DomainValidationError("Debe incluir al menos un detalle")

    cliente_id = payload.get("cliente_id")
    if cliente_id is not None:
        if db.get(Cliente, cliente_id) is None:
            raise EntityNotFoundError("Cliente", cliente_id)

    canal_venta = payload.get("canal_venta", "feria")
    metodo_pago = payload.get("metodo_pago")
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
            raise EntityNotFoundError("Producto", producto_id)
        if variante_id is not None:
            variante = db.get(VarianteProducto, variante_id)
            if variante is None or variante.producto_id != producto_id:
                raise DomainValidationError("variante_id no pertenece al producto")

        costo_unitario = calcular_costo_produccion(db, producto_id, variante_id)
        lineas_costo.append(costo_unitario)
        lineas_subtotal.append(cantidad * precio_unitario)

        for insumo_id, qty in explosion_materiales(db, producto_id, variante_id, cantidad).items():
            explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty

    descontar_stock(db, explosiones)

    total_venta = Decimal(sum(lineas_subtotal)) * descuento_factor
    es_regalo = bool(payload.get("es_regalo", False))
    if es_regalo:
        total_venta = Decimal("0")
    venta = Venta(
        cliente_id=cliente_id,
        canal_venta=canal_venta,
        metodo_pago=metodo_pago,
        descuento_porcentaje=descuento,
        total_venta=total_venta,
        es_regalo=es_regalo,
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
        raise DomainValidationError(
            "Conflicto al registrar la venta; no se persistió nada",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise


def _explosion_venta(db: Session, venta: Venta) -> dict[int, Decimal]:
    """Aggregate the current material explosion of a venta's detail lines.

    Sums ``explosion_materiales`` per existing DetalleVenta (quantity + variant
    as sold). Read-only: no locks, no commits — safe inside the caller's
    transaction.
    """
    explosiones: dict[int, Decimal] = {}
    for detalle in venta.detalles:
        for insumo_id, qty in explosion_materiales(
            db, detalle.producto_id, detalle.variante_id, detalle.cantidad
        ).items():
            explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty
    return explosiones


def actualizar_venta(db: Session, venta_id: int, payload: dict) -> Venta:
    """Full update of a venta in ONE atomic transaction.

    Payload is a plain dict mirroring VentaCreate (``cliente_id``,
    ``canal_venta``, ``descuento_porcentaje``, ``es_regalo``, ``detalles``).
    The old material explosion is RESTORED into stock first, then the new
    payload is validated exactly like ``registrar_venta`` (404 missing
    producto/cliente, 400 foreign variante) and its explosion is deducted with
    FOR UPDATE (409 if insufficient — checked against the real available stock,
    since the old units are already back). Fields are updated (``fecha`` is
    NEVER touched), old detail lines are replaced by new ones with a fresh
    ``costo_unitario_aplicado`` snapshot, and the total is recalculated. There
    is a SINGLE commit at the end; ANY exception rolls everything back (the
    reponed stock and the new lines alike), so a failed edit leaves the venta
    and the stock exactly as they were.
    """
    venta = db.get(Venta, venta_id, with_for_update=True)
    if venta is None:
        raise EntityNotFoundError("Venta", venta_id)
    if venta.estado == DocumentState.CANCELLED.value:
        raise DomainValidationError("No se puede editar una venta anulada")

    detalles = payload["detalles"]
    if not detalles:
        raise DomainValidationError("Debe incluir al menos un detalle")

    cliente_id = payload.get("cliente_id")
    if cliente_id is not None:
        if db.get(Cliente, cliente_id) is None:
            raise EntityNotFoundError("Cliente", cliente_id)

    canal_venta = payload.get("canal_venta", "feria")
    metodo_pago = payload.get("metodo_pago")
    descuento = Decimal(payload.get("descuento_porcentaje", "0"))
    descuento_factor = Decimal("1") - descuento / Decimal("100")

    # 1) Restore the CURRENT stock (the venta as sold).
    reponer_stock(db, _explosion_venta(db, venta))
    # A FLUSH (not a commit) is required BEFORE the new deduction: both stock
    # helpers re-read with populate_existing + FOR UPDATE, so without it the
    # second re-read would clobber the session's pending restock with the stale
    # committed row and double-deduct.
    db.flush()

    # 2) Validate the new payload and build its explosion (mirrors
    #    registrar_venta); the caller's rollback undoes the restock above.
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
            raise EntityNotFoundError("Producto", producto_id)
        if variante_id is not None:
            variante = db.get(VarianteProducto, variante_id)
            if variante is None or variante.producto_id != producto_id:
                raise DomainValidationError("variante_id no pertenece al producto")

        costo_unitario = calcular_costo_produccion(db, producto_id, variante_id)
        lineas_costo.append(costo_unitario)
        lineas_subtotal.append(cantidad * precio_unitario)

        for insumo_id, qty in explosion_materiales(db, producto_id, variante_id, cantidad).items():
            explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty

    descontar_stock(db, explosiones)

    # 3) Recalculate the total and replace the fields + detail lines.
    total_venta = Decimal(sum(lineas_subtotal)) * descuento_factor
    es_regalo = bool(payload.get("es_regalo", False))
    if es_regalo:
        total_venta = Decimal("0")

    venta.cliente_id = cliente_id
    venta.canal_venta = canal_venta
    venta.metodo_pago = metodo_pago
    venta.descuento_porcentaje = descuento
    venta.es_regalo = es_regalo
    venta.total_venta = total_venta
    # fecha is deliberately NOT touched.

    for detalle in list(venta.detalles):
        db.delete(detalle)
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
        raise DomainValidationError(
            "Conflicto al actualizar la venta; no se persistió nada",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise


def anular_venta(db: Session, venta_id: int) -> Venta:
    """Anular (soft-cancel) a venta in ONE atomic transaction.

    NOT a physical delete: the venta's current material explosion is restored
    into stock (``reponer_stock``) and ``estado`` is marked 'anulada', keeping
    the history (consistent with the es_regalo flag philosophy). 404 when the
    venta does not exist, 400 when it is already anulada. A single commit at
    the end; any exception rolls everything back.
    """
    venta = db.get(Venta, venta_id, with_for_update=True)
    if venta is None:
        raise EntityNotFoundError("Venta", venta_id)
    if venta.estado == DocumentState.CANCELLED.value:
        raise DomainValidationError("La venta ya está anulada")

    reponer_stock(db, _explosion_venta(db, venta))
    try:
        venta.transition_to(DocumentState.CANCELLED)
        db.commit()
        db.refresh(venta)
        return venta
    except IntegrityError:
        db.rollback()
        raise DomainValidationError(
            "Conflicto al anular la venta; no se persistió nada",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise
