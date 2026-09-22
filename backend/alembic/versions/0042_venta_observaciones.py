"""Sale notes persisted (0042).

- `Ventas.observaciones` TEXT NULL: free notes per sale (gift wrap,
  delivery, discount context). NULL = none.

Idempotent guards: exact column probing. Downgrade drops the column.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0042_venta_observaciones"
down_revision: str | None = "0041_prenda_venta"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "Ventas"
COLUMN = "observaciones"


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    try:
        return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]
    except Exception:
        return False


def upgrade() -> None:
    if _has_column(TABLE, COLUMN):
        return
    op.add_column(TABLE, sa.Column(COLUMN, sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP COLUMN IF EXISTS "{COLUMN}"'))
