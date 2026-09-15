"""Lote por cantidad: Productos.stock_actual + pedidos_produccion.fase/snapshot.

- `Productos.stock_actual` NUMERIC(15,4) NOT NULL DEFAULT 0: finished units
  on hand (agreed decision: quantity column, NOT per-garment rows).
- `pedidos_produccion.fase` VARCHAR(20) NOT NULL DEFAULT 'corte' with CHECK
  (corte | costura | acabados | calidad | listo): workshop phase advance.
- `pedidos_produccion.costo_unitario_snapshot` NUMERIC(15,4) NULL: unit-cost
  snapshot taken once by completar_lote at lot completion.

Idempotent guards (style 0014/0022/0024): exact table/column/check probing,
never CAST(:table AS regclass). Downgrade drops the CHECK and the columns.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0030_produccion_fase_stock"
down_revision: str | None = "0029_purge_ghost_oct25"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

CK_PEDIDO_FASE = "ck_pedidos_produccion_fase"
PEDIDO_FASE_CHECK = "fase IN ('corte', 'costura', 'acabados', 'calidad', 'listo')"


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


def _has_check(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint c JOIN pg_class cl "
                "ON cl.oid = c.conrelid "
                "WHERE c.conname = :name AND cl.relname = :table "
                "AND c.contype = 'c'"
            ),
            {"name": name, "table": table},
        ).scalar()
        return res is not None
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table("Productos") and not _has_column("Productos", "stock_actual"):
        op.add_column(
            "Productos",
            sa.Column(
                "stock_actual",
                sa.Numeric(15, 4),
                nullable=False,
                server_default="0",
            ),
        )
    if _has_table("pedidos_produccion"):
        if not _has_column("pedidos_produccion", "fase"):
            op.add_column(
                "pedidos_produccion",
                sa.Column("fase", sa.String(20), nullable=False, server_default="corte"),
            )
        # Normalize legacy/out-of-range values (never delete rows, 0024 style).
        bind.execute(
            sa.text(
                "UPDATE pedidos_produccion SET fase = 'corte' "
                "WHERE fase NOT IN ('corte', 'costura', 'acabados', 'calidad', 'listo')"
            )
        )
        if not _has_check("pedidos_produccion", CK_PEDIDO_FASE):
            op.create_check_constraint(
                CK_PEDIDO_FASE, "pedidos_produccion", PEDIDO_FASE_CHECK
            )
        if not _has_column("pedidos_produccion", "costo_unitario_snapshot"):
            op.add_column(
                "pedidos_produccion",
                sa.Column("costo_unitario_snapshot", sa.Numeric(15, 4), nullable=True),
            )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: both names are quoted - unquoted identifiers fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(
        sa.text(
            "ALTER TABLE pedidos_produccion DROP CONSTRAINT IF EXISTS "
            f'"{CK_PEDIDO_FASE}"'
        )
    )
    bind.execute(
        sa.text(
            'ALTER TABLE pedidos_produccion DROP COLUMN IF EXISTS "costo_unitario_snapshot"'
        )
    )
    bind.execute(sa.text('ALTER TABLE pedidos_produccion DROP COLUMN IF EXISTS "fase"'))
    bind.execute(sa.text('ALTER TABLE "Productos" DROP COLUMN IF EXISTS "stock_actual"'))
