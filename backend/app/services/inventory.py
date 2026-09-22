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
from app.models.produccion import PrendaConfeccionada
from app.models.productos import BomInsumo, BomProducto, Producto, VarianteProducto
from app.models.ventas import DetalleVenta, DocumentState, Venta
from app.services.costos import _lineas_insumo_efectivas, calcular_costo_produccion

# P1-6: canonical canal/metodo values (0010 seeds). Used as fallback when the
# maestros tables are unavailable; otherwise membership is read from maestros.
CANALES_CANONICOS = frozenset({"web", "whatsapp", "instagram", "feria", "showroom_pereira"})
METODOS_CANONICOS = frozenset({"efectivo", "transferencia", "tarjeta", "contraentrega"})


def _codigos_maestros(db: Session, tabla: str, fallback: frozenset[str]) -> frozenset[str]:
    """Active maestro codigos for tabla, or fallback when the table is missing.

    Only rows with activo IS DISTINCT FROM false count — a deactivated canal
    or metodo stays valid for history but is rejected for new sales.
    Plain text SQL keeps this independent of the maestros models.
    """
    from sqlalchemy import text as _text

    try:
        rows = db.execute(
            _text(f"SELECT codigo FROM {tabla} WHERE activo IS DISTINCT FROM false")
        ).scalars().all()
        validos = frozenset(r for r in rows if r)
        return validos or fallback
    except Exception:
        db.rollback()
        return fallback


def _validar_canal_metodo(db: Session, canal_venta: str, metodo_pago: str | None) -> None:
    """P1-6: canal/metodo must exist in maestros (422 otherwise).

    Keeps the pre-0024 contract (unknown values -> 422, as pydantic Literal
    did) while accepting any maestro-defined codigo — the DB FK is the hard
    backstop against races (deleted canal between validation and commit).
    """
    canales = _codigos_maestros(db, "maestros_canales_venta", CANALES_CANONICOS)
    if canal_venta not in canales:
        raise DomainValidationError(
            f"canal_venta '{canal_venta}' no existe en maestros", status_code=422
        )
    if metodo_pago is not None:
        metodos = _codigos_maestros(db, "maestros_metodos_pago", METODOS_CANONICOS)
        if metodo_pago not in metodos:
            raise DomainValidationError(
                f"metodo_pago '{metodo_pago}' no existe en maestros", status_code=422
            )


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


def _bloquear_productos(db: Session, producto_ids) -> dict[int, Producto]:
    """Lock Producto rows FIRST, before any stock mutation in the transaction.

    A locked re-read (``populate_existing=True``) cascades refresh through the
    selectin chain (producto -> bom_insumos -> insumo) and WIPES a pending
    insumo deduction/restock made earlier in the same transaction — the exact
    failure completar_lote hit. So callers lock every touched producto up
    front, then mutate insumos and the already-locked producto instances with
    plain attribute writes (never another locked re-read) until commit.
    Unknown producto raises 404.
    """
    bloqueados: dict[int, Producto] = {}
    for producto_id in sorted(producto_ids):
        producto = db.get(
            Producto, producto_id, with_for_update=True, populate_existing=True
        )
        if producto is None:
            raise EntityNotFoundError("Producto", producto_id)
        bloqueados[producto_id] = producto
    return bloqueados


def _descontar_producto_bloqueado(producto: Producto, cantidad: Decimal) -> None:
    """Subtract finished units from an already-locked Producto (no re-read).

    Legacy NULL stock counts as 0. Insufficient units raise 409 — the caller
    owns the rollback, no commit here.
    """
    disponible = producto.stock_actual or Decimal("0")
    if disponible < cantidad:
        raise DomainValidationError(
            f"Stock insuficiente de producto '{producto.nombre}': "
            f"requiere {cantidad}, disponible {disponible}",
            status_code=409,
        )
    producto.stock_actual = disponible - cantidad


def _reponer_producto_bloqueado(producto: Producto, cantidad: Decimal) -> None:
    """Restore finished units into an already-locked Producto (no re-read).

    No commit here — the caller owns the transaction.
    """
    producto.stock_actual = (producto.stock_actual or Decimal("0")) + cantidad


def _agregado_por_producto(detalles: list) -> dict[int, Decimal]:
    """Sum quantities per producto_id across detail lines (dicts or ORM rows)."""
    agregado: dict[int, Decimal] = {}
    for detalle in detalles:
        if isinstance(detalle, dict):
            producto_id = detalle["producto_id"]
            cantidad = Decimal(detalle["cantidad"])
        else:
            producto_id = detalle.producto_id
            cantidad = Decimal(detalle.cantidad)
        agregado[producto_id] = agregado.get(producto_id, Decimal("0")) + cantidad
    return agregado


def _consumir_unidades(
    db: Session, venta_id: int, producto_id: int, variante_id: int | None, cantidad: Decimal
) -> Decimal:
    """Sell finished units first: flip oldest `disponible` rows to `vendida`.

    Exact variante match; generic lines (variante NULL) match producto-linked
    generic rows. Linked to the sale for reversal. Returns the remainder that
    must come out of Producto.stock_actual (0 when units cover it).
    """
    stmt = select(PrendaConfeccionada).where(PrendaConfeccionada.estado == "disponible")
    if variante_id is not None:
        stmt = stmt.where(PrendaConfeccionada.variante_id == variante_id)
    else:
        stmt = stmt.where(
            PrendaConfeccionada.producto_id == producto_id,
            PrendaConfeccionada.variante_id.is_(None),
        )
    rows = list(db.scalars(stmt.order_by(PrendaConfeccionada.id).with_for_update()).all())
    tomar = min(len(rows), int(cantidad))
    for r in rows[:tomar]:
        r.estado = "vendida"
        r.venta_id = venta_id
    return cantidad - tomar


def _contar_prendas_disponibles(
    db: Session, producto_id: int, variante_id: int | None
) -> int:
    """Count `disponible` prendas for a (producto, variante) without locking.

    Read-only availability probe used to decide whether a sale is pure-stock
    (Perchero covers everything → no insumos moves) or needs raw consumption.
    """
    from sqlalchemy import func as _func

    stmt = (
        select(_func.count())
        .select_from(PrendaConfeccionada)
        .where(PrendaConfeccionada.estado == "disponible")
    )
    if variante_id is not None:
        stmt = stmt.where(PrendaConfeccionada.variante_id == variante_id)
    else:
        stmt = stmt.where(
            PrendaConfeccionada.producto_id == producto_id,
            PrendaConfeccionada.variante_id.is_(None),
        )
    return int(db.scalar(stmt) or 0)


def _explosion_para_cantidad(
    db: Session, producto_id: int, variante_id: int | None, cantidad: Decimal
) -> dict[int, Decimal]:
    """Material explosion for an exact quantity (empty when cantidad <= 0)."""
    if cantidad <= 0:
        return {}
    return explosion_materiales(db, producto_id, variante_id, cantidad)


def _devolver_unidades(
    db: Session, venta_id: int, producto_id: int, variante_id: int | None, cantidad: Decimal
) -> Decimal:
    """Flip back up to `cantidad` of this sale's `vendida` rows to disponible.

    Only rows still marked `vendida` move (owner manual edits are never
    double-restored); venta_id stays as history. Returns the remainder that
    must be reponed into Producto.stock_actual.
    """
    stmt = select(PrendaConfeccionada).where(
        PrendaConfeccionada.venta_id == venta_id,
        PrendaConfeccionada.estado == "vendida",
    )
    if variante_id is not None:
        stmt = stmt.where(PrendaConfeccionada.variante_id == variante_id)
    else:
        stmt = stmt.where(
            PrendaConfeccionada.producto_id == producto_id,
            PrendaConfeccionada.variante_id.is_(None),
        )
    rows = list(db.scalars(stmt.order_by(PrendaConfeccionada.id).with_for_update()).all())
    tomar = min(len(rows), int(cantidad))
    for r in rows[:tomar]:
        r.estado = "disponible"
    return cantidad - tomar


def registrar_venta(db: Session, payload: dict) -> Venta:
    """Register a sale and deduct stock in ONE atomic commit.

    Payload is a plain dict mirroring the future VentaCreate schema field names
    (so a pydantic schema can be passed via ``.model_dump()`` by the routes):
    ``cliente_id``, ``canal_venta``, ``descuento_porcentaje``,
    ``codigo_descuento``, ``motivo_descuento`` and ``detalles``
    (a list of ``{producto_id, variante_id, cantidad, precio_unitario}``).

    Per line it snapshots ``costo_unitario_aplicado`` = the product's current
    production cost (read from ``Insumo.costo_promedio_actual`` through the
    reusable cost engine), aggregates the flat explosion across lines, deducts
    stock with FOR UPDATE (409 if insufficient, all-or-nothing) — insumos AND
    the finished units in Producto.stock_actual (409 if short) — then commits
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
    _validar_canal_metodo(db, canal_venta, metodo_pago)
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

    # Pure-stock fast path (Perchero): when every line is fully covered by
    # `disponible` prendas, the sale moves finished units only — insumos were
    # already consumed when those units were produced/loaded, so deducting
    # them again 409s on real sales (e.g. Tote with 0 raw stock). Mixed or
    # uncovered sales keep the legacy strict path (insumos full).
    cubre_todo = True
    for detalle in detalles:
        disp = _contar_prendas_disponibles(
            db, detalle["producto_id"], detalle.get("variante_id")
        )
        if disp < int(Decimal(detalle["cantidad"])):
            cubre_todo = False
            break
    if not cubre_todo:
        for detalle in detalles:
            for insumo_id, qty in explosion_materiales(
                db,
                detalle["producto_id"],
                detalle.get("variante_id"),
                Decimal(detalle["cantidad"]),
            ).items():
                explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty

    # Lock finished-stock rows BEFORE any mutation (see _bloquear_productos):
    # a locked re-read after descontar_stock would cascade-refresh the selectin
    # chain and wipe the pending insumo deduction.
    agregados = _agregado_por_producto(detalles)
    bloqueados = _bloquear_productos(db, agregados.keys())

    if explosiones:
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
        codigo_descuento=(str(payload.get("codigo_descuento")).strip() or None)
        if payload.get("codigo_descuento") is not None
        else None,
        motivo_descuento=payload.get("motivo_descuento"),
        observaciones=(str(payload.get("observaciones")).strip() or None)
        if payload.get("observaciones") is not None
        else None,
        total_venta=total_venta,
        es_regalo=es_regalo,
        # Document-state domain (ck_ventas_estado): a new sale is confirmed.
        # The legacy 'completada' value violates the CHECK on
        # migrations-built schemas and 409s every POST /ventas.
        estado=DocumentState.CONFIRMED.value,
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
    # Flush to obtain venta.id before linking finished units (0041).
    # No commit yet — everything below still rolls back atomically.
    db.flush()

    # Finished units first (Perchero/talla): flip oldest `disponible` rows to
    # `vendida` linked to this venta; only the remainder leaves
    # Producto.stock_actual (409 if short). Insumos already deducted above.
    restos: dict[int, Decimal] = {}
    for detalle in detalles:
        resto = _consumir_unidades(
            db,
            venta.id,
            detalle["producto_id"],
            detalle.get("variante_id"),
            Decimal(detalle["cantidad"]),
        )
        if resto > 0:
            restos[detalle["producto_id"]] = (
                restos.get(detalle["producto_id"], Decimal("0")) + resto
            )
    # Finished-unit stock moves with the insumo stock in the same transaction:
    # every sold unit not covered by prendas leaves Producto.stock_actual.
    for producto_id, qty in sorted(restos.items()):
        _descontar_producto_bloqueado(bloqueados[producto_id], qty)

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
    The old material explosion is RESTORED into stock first (insumos and the
    finished Producto.stock_actual units), then the new
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
    _validar_canal_metodo(db, canal_venta, metodo_pago)
    descuento = Decimal(payload.get("descuento_porcentaje", "0"))
    descuento_factor = Decimal("1") - descuento / Decimal("100")

    # 1) Restore the CURRENT stock (the venta as sold) — insumos and the
    #    finished units sold. Every touched producto (old AND new lines) is
    #    locked BEFORE any mutation: a later locked re-read would wipe pending
    #    changes (see _bloquear_productos).
    agregados_viejos = _agregado_por_producto(list(venta.detalles))
    agregados_nuevos = _agregado_por_producto(detalles)
    bloqueados = _bloquear_productos(
        db, set(agregados_viejos) | set(agregados_nuevos)
    )
    # Flip back this sale's `vendida` rows first (0041); only the remainder
    # not covered by prendas restores insumos + Producto.stock. Old sales
    # without linked rows return full cantidad (backward compatible); pure-stock
    # sales return 0 remainder (no raw moves, symmetric with registrar).
    restos_viejos: dict[int, Decimal] = {}
    restos_viejos_lineas: list[tuple[int, int | None, Decimal]] = []
    for det in list(venta.detalles):
        resto = _devolver_unidades(
            db, venta.id, det.producto_id, det.variante_id, Decimal(det.cantidad)
        )
        if resto > 0:
            restos_viejos[det.producto_id] = (
                restos_viejos.get(det.producto_id, Decimal("0")) + resto
            )
            restos_viejos_lineas.append((det.producto_id, det.variante_id, resto))
    resto_explosion: dict[int, Decimal] = {}
    for producto_id, variante_id, resto in restos_viejos_lineas:
        for insumo_id, qty in _explosion_para_cantidad(
            db, producto_id, variante_id, resto
        ).items():
            resto_explosion[insumo_id] = resto_explosion.get(insumo_id, Decimal("0")) + qty
    if resto_explosion:
        reponer_stock(db, resto_explosion)
    for producto_id, qty in sorted(restos_viejos.items()):
        _reponer_producto_bloqueado(bloqueados[producto_id], qty)
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

    # Pure-stock fast path (mirrors registrar_venta): post-restore disponibles
    # cover everything → skip raw moves.
    cubre_nuevo = True
    for detalle in detalles:
        disp = _contar_prendas_disponibles(
            db, detalle["producto_id"], detalle.get("variante_id")
        )
        if disp < int(Decimal(detalle["cantidad"])):
            cubre_nuevo = False
            break
    if not cubre_nuevo:
        for detalle in detalles:
            for insumo_id, qty in explosion_materiales(
                db,
                detalle["producto_id"],
                detalle.get("variante_id"),
                Decimal(detalle["cantidad"]),
            ).items():
                explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty

    if explosiones:
        descontar_stock(db, explosiones)

    restos_nuevos: dict[int, Decimal] = {}
    for detalle in detalles:
        resto = _consumir_unidades(
            db,
            venta.id,
            detalle["producto_id"],
            detalle.get("variante_id"),
            Decimal(detalle["cantidad"]),
        )
        if resto > 0:
            restos_nuevos[detalle["producto_id"]] = (
                restos_nuevos.get(detalle["producto_id"], Decimal("0")) + resto
            )
    for producto_id, qty in sorted(restos_nuevos.items()):
        _descontar_producto_bloqueado(bloqueados[producto_id], qty)

    # 3) Recalculate the total and replace the fields + detail lines.
    total_venta = Decimal(sum(lineas_subtotal)) * descuento_factor
    es_regalo = bool(payload.get("es_regalo", False))
    if es_regalo:
        total_venta = Decimal("0")

    venta.cliente_id = cliente_id
    venta.canal_venta = canal_venta
    venta.metodo_pago = metodo_pago
    venta.descuento_porcentaje = descuento
    venta.codigo_descuento = (
        (str(payload.get("codigo_descuento")).strip() or None)
        if payload.get("codigo_descuento") is not None
        else None
    )
    venta.motivo_descuento = payload.get("motivo_descuento")
    venta.observaciones = (
        (str(payload.get("observaciones")).strip() or None)
        if payload.get("observaciones") is not None
        else None
    )
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
    into stock (``reponer_stock``) plus the finished Producto.stock_actual
    units, and ``estado`` is marked 'anulada', keeping
    the history (consistent with the es_regalo flag philosophy). 404 when the
    venta does not exist, 400 when it is already anulada. A single commit at
    the end; any exception rolls everything back.
    """
    venta = db.get(Venta, venta_id, with_for_update=True)
    if venta is None:
        raise EntityNotFoundError("Venta", venta_id)
    if venta.estado == DocumentState.CANCELLED.value:
        raise DomainValidationError("La venta ya está anulada")

    agregados = _agregado_por_producto(list(venta.detalles))
    bloqueados = _bloquear_productos(db, agregados.keys())
    restos: dict[int, Decimal] = {}
    restos_lineas: list[tuple[int, int | None, Decimal]] = []
    for det in list(venta.detalles):
        resto = _devolver_unidades(
            db, venta.id, det.producto_id, det.variante_id, Decimal(det.cantidad)
        )
        if resto > 0:
            restos[det.producto_id] = restos.get(det.producto_id, Decimal("0")) + resto
            restos_lineas.append((det.producto_id, det.variante_id, resto))
    resto_explosion: dict[int, Decimal] = {}
    for producto_id, variante_id, resto in restos_lineas:
        for insumo_id, qty in _explosion_para_cantidad(
            db, producto_id, variante_id, resto
        ).items():
            resto_explosion[insumo_id] = resto_explosion.get(insumo_id, Decimal("0")) + qty
    if resto_explosion:
        reponer_stock(db, resto_explosion)
    for producto_id, qty in sorted(restos.items()):
        _reponer_producto_bloqueado(bloqueados[producto_id], qty)
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
