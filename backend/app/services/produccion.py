"""Production lot completion — unit stock with workshop phases.

A production order manufactures ``cantidad`` finished units of a product.
When the order reaches the end of the line (``fase == 'listo'`` or
``estado == 'completado'``) ``completar_lote`` runs ONCE, atomically:

1. Flat BOM explosion for N = cantidad (``explosion_materiales``).
2. Per-insumo availability check with FULL detail (every short insumo with
   required vs. available) -> 409, nothing touched.
3. ``descontar_stock`` (FOR UPDATE, all-or-nothing) for the insumos.
4. Create N ``PrendaConfeccionada`` rows in ``disponible`` (linked to the
   pedido, with the unit-cost snapshot) — the lot FEEDS the Perchero stock,
   which is the single source of truth for sales. ``Producto.stock_actual``
   is legacy quantity stock and is NOT credited.
5. Unit-cost snapshot via ``calcular_costo_produccion`` into the lot record
   (``pedido.costo_unitario_snapshot``) + ``cantidad_producida = cantidad``.
6. Additive real-cost info (``mano_obra_real`` from all TiempoFase rows and
    ``energia_real`` from 'costura' rows only x global rates) returned for
    the response — manual ``Producto.mano_obra``/``cif_energia`` estimates
    are never overwritten.

No commit here — the caller (PATCH /pedidos-produccion/{id}) owns the single
commit, mirroring the ``descontar_stock`` convention. Re-running on an
already-completed lot is a no-op (guarded by ``cantidad_producida``).
"""

from decimal import Decimal
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DomainValidationError, EntityNotFoundError
from app.models.insumos import Insumo
from app.models.produccion import (
    FASES_PRODUCCION_ORDEN,
    FASES_TIEMPO_ORDEN,
    PedidoProduccion,
    PedidoProduccionEstado,
    PedidoProduccionFase,
    PrendaConfeccionada,
    PrendaEstado,
    TiempoFase,
)
from app.models.productos import Producto, VarianteProducto
from app.services.costos import calcular_costo_produccion, tasas_costeo
from app.services.inventory import descontar_stock, explosion_materiales


def pedido_esta_completado(pedido: PedidoProduccion) -> bool:
    """True once the lot reached the end of the line by either signal."""
    return (
        pedido.fase == PedidoProduccionFase.LISTO
        or pedido.estado == PedidoProduccionEstado.COMPLETADO
    )


def validar_avance_fase(fase_actual: str | None, fase_nueva: str) -> None:
    """Enforce phase moves on the workshop order (422 unknown).

    Same-phase PATCH is a no-op (allowed). Forward must step exactly one
    position in ``FASES_PRODUCCION_ORDEN`` (no skips). Backward (devolución
    por reproceso, e.g. calidad -> costura) may target ANY earlier phase.
    'listo' is terminal: the lot was already credited by completar_lote, so
    nothing moves out of it. Rework time is EDITED onto the existing
    TiempoFase row (uq_tiempos_pedido_fase: one row per phase).
    """
    if fase_nueva not in FASES_PRODUCCION_ORDEN:
        raise DomainValidationError(
            f"fase '{fase_nueva}' inválida; valores: {', '.join(FASES_PRODUCCION_ORDEN)}",
            status_code=422,
        )
    actual = fase_actual or PedidoProduccionFase.CORTE
    if fase_nueva == actual:
        return
    idx_actual = (
        FASES_PRODUCCION_ORDEN.index(actual)
        if actual in FASES_PRODUCCION_ORDEN
        else 0
    )
    idx_nueva = FASES_PRODUCCION_ORDEN.index(fase_nueva)
    if actual == PedidoProduccionFase.LISTO:
        raise DomainValidationError(
            f"El pedido ya está '{actual}' (lote acreditado): sin movimientos"
        )
    if idx_nueva < idx_actual:
        return  # devolución por reproceso a cualquier fase anterior
    if idx_nueva > idx_actual + 1:
        siguiente = FASES_PRODUCCION_ORDEN[idx_actual + 1]
        raise DomainValidationError(
            f"Avance secuencial: de '{actual}' solo se puede pasar a '{siguiente}'"
        )


def validar_fase_tiempo(fase_pedido: str | None, fase: str) -> None:
    """Enforce that a TiempoFase log belongs to a reachable workshop phase.

    422 for unknown phases and for ``listo`` (closing the lot is not worked
    time). 400 when the phase is ahead of the order (e.g. logging
    ``costura`` while the pedido is still in ``corte``). Logging a phase at
    or behind the current one is allowed — the row records work done.
    """
    if fase not in FASES_TIEMPO_ORDEN:
        raise DomainValidationError(
            f"fase '{fase}' inválida para tiempos; "
            f"valores: {', '.join(FASES_TIEMPO_ORDEN)}",
            status_code=422,
        )
    actual = fase_pedido or PedidoProduccionFase.CORTE
    idx_actual = (
        FASES_PRODUCCION_ORDEN.index(actual)
        if actual in FASES_PRODUCCION_ORDEN
        else 0
    )
    idx_fase = FASES_PRODUCCION_ORDEN.index(fase)
    if idx_fase > idx_actual:
        raise DomainValidationError(
            f"No se puede registrar tiempo de '{fase}': "
            f"el pedido está en '{actual}'"
        )


def totales_tiempos(db: Session, pedido_id: int) -> dict[str, Decimal]:
    """Read-time real-cost totals for a lot (no persistence, no estimates touched).

    Returns minutos/mano/energia as Decimal; all zero when no rows exist.
    ENERGY applies ONLY to fase 'costura' (sewing machines): corte,
    acabados and calidad are manual work with zero energy. Labor (mano de
    obra) counts ALL phases; minutos counts ALL phases (it is time).
    Callers map all-zero to ``None`` on response models so "no data" stays
    distinguishable from "zero minutes worked".
    """
    rows = db.scalars(
        select(TiempoFase).where(TiempoFase.pedido_id == pedido_id)
    ).all()
    tasa_mano, tasa_energia = tasas_costeo(db)
    minutos = sum((r.minutos_reales for r in rows), Decimal("0"))
    minutos_costura = sum(
        (r.minutos_reales for r in rows if r.fase == "costura"), Decimal("0")
    )
    return {
        "minutos_totales": minutos,
        "mano_obra_real": minutos * tasa_mano,
        "energia_real": minutos_costura * tasa_energia,
    }


def completar_lote(db: Session, pedido: PedidoProduccion) -> dict[str, Decimal]:
    """Complete a production lot: consume insumos, feed Perchero stock.

    Idempotency is two-layered: the route only invokes on the transition INTO
    listo/completado, and this service no-ops when ``cantidad_producida``
    already covers ``cantidad`` (409 detail and 0 double-credit on retry).
    Raises 409 with per-insumo required-vs-available detail on shortage, 404
    on missing producto/insumo. No commit — caller owns the transaction.

    Returns the unit-cost snapshot plus the additive real-cost info
    (mano_obra_real from all TiempoFase rows, energia_real from 'costura'
    rows only, x global rates, zero when no tiempos exist). Producto.mano_obra/cif_energia are NEVER
    overwritten here — manual estimates stay; the totals let a later slice
    propose updating them.
    """
    if (pedido.cantidad_producida or 0) >= pedido.cantidad and pedido.cantidad_producida:
        totales = totales_tiempos(db, pedido.id)
        return {
            "costo_unitario": pedido.costo_unitario_snapshot
            or calcular_costo_produccion(db, pedido.producto_id, pedido.variante_id),
            "minutos_totales": totales["minutos_totales"],
            "mano_obra_real": totales["mano_obra_real"],
            "energia_real": totales["energia_real"],
        }

    cantidad = Decimal(pedido.cantidad)
    # Lock the producto FIRST, before any stock mutation. A locked re-read
    # with populate_existing=True cascades refresh through the selectin chain
    # (producto -> bom_insumos -> insumo) and would wipe a pending insumo
    # deduction if done after descontar_stock — so the lock lives here even
    # though the lot no longer mutates Producto.stock_actual (legacy).
    producto = db.get(
        Producto, pedido.producto_id, with_for_update=True, populate_existing=True
    )
    if producto is None:
        raise EntityNotFoundError("Producto", pedido.producto_id)

    explosion = explosion_materiales(
        db, pedido.producto_id, pedido.variante_id, cantidad
    )

    # Full-detail availability pass (locks rows; no mutation). descontar_stock
    # below aborts on the FIRST shortage only, so this pass builds the 409
    # with EVERY short insumo instead.
    faltantes: list[str] = []
    for insumo_id in sorted(explosion):
        insumo = db.get(Insumo, insumo_id, with_for_update=True, populate_existing=True)
        if insumo is None:
            raise EntityNotFoundError("Insumo", insumo_id)
        requerido = explosion[insumo_id]
        disponible = insumo.stock_actual or Decimal("0")
        if disponible < requerido:
            faltantes.append(
                f"'{insumo.nombre}' (requiere {requerido}, disponible {disponible})"
            )
    if faltantes:
        raise DomainValidationError(
            "Stock insuficiente para completar el lote: " + "; ".join(faltantes),
            status_code=409,
        )

    descontar_stock(db, explosion)

    costo_unitario = calcular_costo_produccion(
        db, pedido.producto_id, pedido.variante_id
    )
    # The lot feeds the Perchero: one `disponible` row per finished unit, so
    # sales always move finished stock and never re-consume raw insumos.
    # Talla mirrors the variante naming convention ("M - Rojo" -> "M");
    # generic lots (no variante) stay talla-less like manual generic loads.
    talla: str | None = None
    if pedido.variante_id is not None:
        variante = db.get(VarianteProducto, pedido.variante_id)
        if variante is not None:
            talla = (variante.nombre_variante.split(" - ")[0].strip() or None)
    hoy = date.today()
    for _ in range(int(cantidad)):
        db.add(
            PrendaConfeccionada(
                producto_id=pedido.producto_id,
                variante_id=pedido.variante_id,
                talla=talla,
                estado=PrendaEstado.DISPONIBLE,
                costo_real=costo_unitario,
                fecha_confeccion=hoy,
                pedido_id=pedido.id,
            )
        )

    pedido.costo_unitario_snapshot = costo_unitario
    pedido.cantidad_producida = pedido.cantidad
    totales = totales_tiempos(db, pedido.id)
    return {
        "costo_unitario": costo_unitario,
        "minutos_totales": totales["minutos_totales"],
        "mano_obra_real": totales["mano_obra_real"],
        "energia_real": totales["energia_real"],
    }
