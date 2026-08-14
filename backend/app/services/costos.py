from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BomCycleDetectedError, EntityNotFoundError
from app.models.productos import BomInsumo, BomProducto, Producto
from app.schemas.costo import CostoLineaRead


def _lineas_insumo_efectivas(rows: list[BomInsumo], variante_id: int | None) -> list[BomInsumo]:
    """Pick the effective BOM insumo lines for a variant.

    A row with variante_id NULL is the base rule for ALL variants; a row with
    variante_id == X overrides (not adds to) the base rule for variant X only.
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

    # BOM traversal happens only for manufactured products; non-fabricated or
    # no-BOM products cost exactly their fixed operating costs.
    if not producto.requiere_fabricacion:
        memo[key] = fijos
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
        return fijos

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
        memo[key] = fijos
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
        return fijos

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
