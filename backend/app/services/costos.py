from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BomCycleDetectedError, EntityNotFoundError
from app.models.maestros import ParametrosCosteo
from app.models.productos import BomInsumo, BomProducto, Producto
from app.schemas.costo import CostoLineaRead


def tasas_costeo(db: Session) -> tuple[Decimal, Decimal]:
    """Global (mano/min, energia/min) rates. Read-only: never auto-creates.

    Missing singleton row reads as 0/0 so GET endpoints stay side-effect
    free; the singleton is created by GET/PATCH /maestros/parametros-costeo.
    Lives here (not produccion.py) so the cost engine owns its rate source;
    produccion.py re-imports it for real-time lot totals.
    """
    row = db.get(ParametrosCosteo, 1)
    if row is None:
        return Decimal("0"), Decimal("0")
    return (
        row.costo_minuto_costura or Decimal("0"),
        row.costo_minuto_energia or Decimal("0"),
    )


def costo_mano_energia_estandar(
    db: Session, producto: Producto
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """Standard labor + energy cost for one product level.

    Returns (mano, energia, minutos_base, minutos_costura, tasa_mano,
    tasa_energia) so the breakdown lines reuse exact rates (no division).

    - Any per-phase standard time set (0036) -> automatic:
      mano = total_min x tasa_mano, energia = costura_min x tasa_energia
      (energy only on costura: sewing machines; same rule as TiempoFase).
    - No times -> stored manual Producto.mano_obra / cif_energia (legacy
      fallback; NULL reads as 0). BOM entry (0036 decision) never writes here.
    """
    tiempos = [
        producto.tiempo_corte_min,
        producto.tiempo_costura_min,
        producto.tiempo_acabados_min,
        producto.tiempo_calidad_min,
    ]
    if any(v is not None for v in tiempos):
        tasa_mano, tasa_energia = tasas_costeo(db)
        total_min = Decimal(sum(int(v or 0) for v in tiempos))
        costura_min = Decimal(int(producto.tiempo_costura_min or 0))
        return (
            total_min * tasa_mano,
            costura_min * tasa_energia,
            total_min,
            costura_min,
            tasa_mano,
            tasa_energia,
        )
    uno = Decimal("1")
    mano = producto.mano_obra if producto.mano_obra is not None else Decimal("0")
    energia = producto.cif_energia if producto.cif_energia is not None else Decimal("0")
    return (mano, energia, uno, uno, mano, energia)


def _lineas_insumo_efectivas(rows: list[BomInsumo], variante_id: int | None) -> list[BomInsumo]:
    """Pick the effective BOM insumo lines for a variant.

    A row with variante_id NULL is the base rule for ALL variants; a row with
    variante_id == X overrides (not adds to) the base rule for variant X only.

    Repeated lines SUM: several rows may share the same (producto, insumo,
    variante) — e.g. one row per garment piece — and every effective row is
    returned so the caller adds each one. The override is cross-level only:
    when ANY variant-X row exists for insumo Y, ALL NULL base rows for Y are
    ignored (`insumo_id in ids_variante`); multiple NULL rows (or multiple X
    rows) still sum among themselves. This already holds with the code below,
    no extra branch needed.
    """
    if variante_id is None:
        return [r for r in rows if r.variante_id is None]
    ids_variante = {r.insumo_id for r in rows if r.variante_id == variante_id}
    efectivas = [r for r in rows if r.variante_id == variante_id]
    efectivas += [r for r in rows if r.variante_id is None and r.insumo_id not in ids_variante]
    efectivas.sort(key=lambda r: r.id)
    return efectivas


def _calcular(
    db: Session,
    producto_id: int,
    variante_id: int | None,
    path: list[int],
    memo: dict[tuple[int, int | None], Decimal],
    lineas_out: list[CostoLineaRead] | None = None,
) -> Decimal:
    """Recursive cost for one product, memoized intra-call.

    - path is the recursion stack on producto_id; a reappearing product aborts
      with 409 (cycle).
    - memo is keyed (producto_id, variante_id) and lives only for this call —
      never cached across calls because Insumo.costo_promedio_actual changes.
    - lineas_out collects the 1-level breakdown ONLY at the root call.
    - Read-only: no locks, no commits — callable inside a Phase-4 FOR UPDATE
      transaction.
    """
    key = (producto_id, variante_id)
    if producto_id in path:
        raise BomCycleDetectedError([*path, producto_id])
    if key in memo:
        return memo[key]

    producto = db.get(Producto, producto_id)
    if producto is None:
        raise EntityNotFoundError("Producto", producto_id)

    fijos = producto.costos_operativos_fijos
    mano_std, energia_std, min_base, min_costura, tasa_mano, tasa_energia = (
        costo_mano_energia_estandar(db, producto)
    )

    def _con_tiempos(base: Decimal) -> Decimal:
        return base + mano_std + energia_std

    def _lineas_tiempos() -> None:
        if lineas_out is None:
            return
        if mano_std != 0:
            lineas_out.append(
                CostoLineaRead(
                    tipo="mano_obra",
                    id=producto_id,
                    nombre=f"Mano de obra ({producto.nombre})",
                    cantidad=min_base,
                    costo_unitario=tasa_mano,
                    costo_total=mano_std,
                )
            )
        if energia_std != 0:
            lineas_out.append(
                CostoLineaRead(
                    tipo="cif_energia",
                    id=producto_id,
                    nombre=f"Energía costura ({producto.nombre})",
                    cantidad=min_costura,
                    costo_unitario=tasa_energia,
                    costo_total=energia_std,
                )
            )

    # BOM traversal happens only for manufactured products; non-fabricated or
    # no-BOM products cost exactly their fixed operating costs.
    if not producto.requiere_fabricacion:
        memo[key] = _con_tiempos(fijos)
        if lineas_out is not None:
            lineas_out.append(
                CostoLineaRead(
                    tipo="operativos_fijos",
                    id=producto_id,
                    nombre=producto.nombre,
                    cantidad=Decimal("1"),
                    costo_unitario=fijos,
                    costo_total=fijos,
                )
            )
            _lineas_tiempos()
        return _con_tiempos(fijos)

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

    if not insumo_rows and not producto_rows:
        memo[key] = _con_tiempos(fijos)
        if lineas_out is not None:
            lineas_out.append(
                CostoLineaRead(
                    tipo="operativos_fijos",
                    id=producto_id,
                    nombre=producto.nombre,
                    cantidad=Decimal("1"),
                    costo_unitario=fijos,
                    costo_total=fijos,
                )
            )
            _lineas_tiempos()
        return _con_tiempos(fijos)

    path.append(producto_id)
    try:
        total = fijos
        for linea in _lineas_insumo_efectivas(insumo_rows, variante_id):
            cantidad_efectiva = linea.cantidad_requerida * (
                Decimal("1") + linea.porcentaje_desperdicio / Decimal("100")
            )
            costo_unitario = linea.insumo.costo_promedio_actual
            subtotal = cantidad_efectiva * costo_unitario
            total += subtotal
            if lineas_out is not None:
                lineas_out.append(
                    CostoLineaRead(
                        tipo="insumo",
                        id=linea.insumo_id,
                        nombre=linea.insumo.nombre,
                        cantidad=cantidad_efectiva,
                        costo_unitario=costo_unitario,
                        costo_total=subtotal,
                    )
                )
        for linea in producto_rows:
            costo_hijo = _calcular(db, linea.producto_incluido_id, variante_id, path, memo)
            subtotal = linea.cantidad * costo_hijo
            total += subtotal
            if lineas_out is not None:
                lineas_out.append(
                    CostoLineaRead(
                        tipo="producto",
                        id=linea.producto_incluido_id,
                        nombre=linea.producto_incluido.nombre,
                        cantidad=linea.cantidad,
                        costo_unitario=costo_hijo,
                        costo_total=subtotal,
                    )
                )
        total = _con_tiempos(total)
        if lineas_out is not None:
            _lineas_tiempos()
        memo[key] = total
        return total
    finally:
        path.pop()


def calcular_costo_produccion(
    db: Session, producto_id: int, variante_id: int | None = None
) -> Decimal:
    """Total production cost for a product (recursive, memoized intra-call)."""
    return _calcular(db, producto_id, variante_id, path=[], memo={})


def desglosar_costo_produccion(
    db: Session, producto_id: int, variante_id: int | None = None
) -> tuple[Decimal, list[CostoLineaRead]]:
    """Total cost plus the 1-level breakdown (one line per direct BOM row)."""
    lineas: list[CostoLineaRead] = []
    total = _calcular(db, producto_id, variante_id, path=[], memo={}, lineas_out=lineas)
    return total, lineas
