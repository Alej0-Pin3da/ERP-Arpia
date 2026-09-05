"""FK pedidos_produccion.cliente_id -> Clientes(id) — clienta que realiza el pedido.

- Adds nullable `cliente_id` column (walk-in orders without client stay NULL).
- FK ON DELETE SET NULL: deleting a client keeps the production history.
- New column starts all-NULL, so no orphan handling is needed.
- Idempotent guards (style 0014/0022): exact table/column/FK checks, never
  CAST(:table AS regclass). Downgrade drops the FK and the column.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026_pedidos_cliente_fk"
down_revision: str | None = "0025_prendas_variante_nullable"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "pedidos_produccion"
COLUMN = "cliente_id"
REF_TABLE = "Clientes"
FK_NAME = "pedidos_produccion_cliente_id_fkey"


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


def _has_fk(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint c JOIN pg_class cl "
                "ON cl.oid = c.conrelid "
                "WHERE c.conname = :name AND cl.relname = :table "
                "AND c.contype = 'f'"
            ),
            {"name": name, "table": table},
        ).scalar()
        return res is not None
    except Exception:
        return False


def upgrade() -> None:
    if not _has_table(TABLE) or not _has_table(REF_TABLE):
        return
    if not _has_column(TABLE, COLUMN):
        op.add_column(TABLE, sa.Column(COLUMN, sa.Integer(), nullable=True))
    if not _has_fk(TABLE, FK_NAME):
        op.create_foreign_key(
            FK_NAME,
            TABLE,
            REF_TABLE,
            [COLUMN],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: both names are quoted - unquoted identifiers fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP CONSTRAINT IF EXISTS "{FK_NAME}"'))
    bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP COLUMN IF EXISTS "{COLUMN}"'))
