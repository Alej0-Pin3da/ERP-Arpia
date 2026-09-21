"""Link sold units back to their sale (0041).

- `prendas_confeccionadas.venta_id` INTEGER NULL FK Ventas.id
  ON DELETE SET NULL: which sale consumed each unit (flip-back on anular /
  PUT-edit / devolución). NULL = never sold or manually managed.
- Nullable, no backfill (history predates the link; only new movements set
  it). Anular flips only its own `vendida` rows, so manual estado edits by
  the owner are never double-restored.

Idempotent guards: exact column probing, never CAST(:table AS regclass).
Downgrade drops the column (FK goes with it).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041_prenda_venta"
down_revision: str | None = "0040_prenda_producto"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "prendas_confeccionadas"
COLUMN = "venta_id"


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    try:
        return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]
    except Exception:
        return False


def upgrade() -> None:
    if _has_column(TABLE, COLUMN):
        return
    op.add_column(
        TABLE,
        sa.Column(
            COLUMN,
            sa.Integer(),
            sa.ForeignKey("Ventas.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(f"ix_{TABLE}_{COLUMN}", TABLE, [COLUMN])


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP COLUMN IF EXISTS "{COLUMN}"'))
