"""BOM insumos allow repeated lines: drop uq_bom_insumos_combo.

- `uq_bom_insumos_combo` on "BOM_Insumos"(producto_id, insumo_id,
  variante_id): repeated lines of the same insumo are legal and SUM (one row
  per garment piece, e.g. Blusa torso + 2 sleeves of the same fabric), so the
  combo uniqueness must go. BomProducto keeps its own `uq_bom_productos_combo`.
- PostgreSQL never enforced the NULL-variante case anyway (NULLs are
  distinct), so dropping only affects variant-scoped rows.

Idempotent guards (style 0030/0031/0032/0033): exact constraint probing via
pg_constraint, never CAST(:table AS regclass). Downgrade re-creates it.

RISK: downgrade fails loudly with a duplicate-key error when repeated lines
exist — dedupe manually, then retry.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0034_bom_insumos_repetidos"
down_revision: str | None = "0033_devolucion_venta_unique"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_unique_constraint(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        return bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint "
                "WHERE conname = :name "
                "AND conrelid = (SELECT oid FROM pg_class WHERE relname = :table)"
            ),
            {"name": name, "table": table},
        ).scalar() is not None
    except Exception:
        return False


def upgrade() -> None:
    if _has_unique_constraint("BOM_Insumos", "uq_bom_insumos_combo"):
        op.drop_constraint("uq_bom_insumos_combo", "BOM_Insumos", type_="unique")


def downgrade() -> None:
    if not _has_unique_constraint("BOM_Insumos", "uq_bom_insumos_combo"):
        op.create_unique_constraint(
            "uq_bom_insumos_combo",
            "BOM_Insumos",
            ["producto_id", "insumo_id", "variante_id"],
        )
