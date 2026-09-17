"""BOM insumo piece label: BOM_Insumos.detalle.

- `BOM_Insumos.detalle` VARCHAR(150) NULL: optional piece label (torso,
  manga, any part) distinguishing repeated lines of the same insumo for
  the workshop.
- Cost/stock neutral: no backfill, existing rows stay NULL; costos and
  explosion ignore the label (repeated lines still SUM by quantity).

Idempotent guards (style 0030/0031/0032/0034): exact column probing, never
CAST(:table AS regclass). Downgrade drops the column.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0035_bom_insumo_detalle"
down_revision: str | None = "0034_bom_insumos_repetidos"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return table in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    try:
        return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]
    except Exception:
        return False


def upgrade() -> None:
    if _has_table("BOM_Insumos") and not _has_column("BOM_Insumos", "detalle"):
        op.add_column(
            "BOM_Insumos",
            sa.Column("detalle", sa.String(150), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text('ALTER TABLE "BOM_Insumos" DROP COLUMN IF EXISTS "detalle"'))
