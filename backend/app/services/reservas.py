"""Stock reservations for open production orders (V6 M4).

Creating a pedido sets aside its full BOM explosion in
``Insumo.stock_reservado``; completing (or deleting) it releases that same
explosion. Both run INSIDE the caller's transaction (no commits here).

Two honesty notes:
- The release recomputes the CURRENT explosion (no per-pedido ledger), so a
  BOM edited mid-flight drifts by the delta. Releases clamp at zero, so
  legacy rows (never reserved) and drift can never drive a balance negative.
- Availability everywhere means ``disponible`` (actual minus reserved).
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.insumos import Insumo
from app.models.produccion import PedidoProduccion
from app.services.inventory import explosion_materiales


def _explosion_pedido(
    db: Session, pedido: PedidoProduccion
) -> dict[int, Decimal]:
    return explosion_materiales(
        db, pedido.producto_id, pedido.variante_id, Decimal(pedido.cantidad)
    )


def reservar_pedido(db: Session, pedido: PedidoProduccion) -> dict[int, Decimal]:
    """Set aside one pedido's BOM explosion (no commit)."""
    explosion = _explosion_pedido(db, pedido)
    for insumo_id in sorted(explosion):
        insumo = db.get(Insumo, insumo_id, with_for_update=True)
        if insumo is None:
            continue
        insumo.stock_reservado = (insumo.stock_reservado or Decimal("0")) + explosion[
            insumo_id
        ]
    db.flush()
    return explosion


def liberar_pedido(db: Session, pedido: PedidoProduccion) -> dict[int, Decimal]:
    """Release one pedido's (recomputed) explosion, clamped at zero (no commit)."""
    explosion = _explosion_pedido(db, pedido)
    for insumo_id in sorted(explosion):
        insumo = db.get(Insumo, insumo_id, with_for_update=True)
        if insumo is None:
            continue
        insumo.stock_reservado = max(
            Decimal("0"),
            (insumo.stock_reservado or Decimal("0")) - explosion[insumo_id],
        )
    db.flush()
    return explosion
