"""FK Compras_Insumos.proveedor_id -> maestros_proveedores(id) (P1-5).

- Compras_Insumos.proveedor_id is nullable (0008 + 20260821_wac re-added it
  without REFERENCES), so ON DELETE SET NULL.
- Orphan rows (proveedor_id with no match in maestros_proveedores) are set
  to NULL before the FK is created — data is never deleted.
- Idempotent guards (_has_table/_has_column/_has_fk with exact pg_class
  match — never CAST(:table AS regclass), which fails on case-sensitive
  tables and poisons the transaction). Downgrade drops the FK only.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022_compras_proveedor_fk"
down_revision: str | None = "0021_backfill_costo_insumos"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

FK_NAME = "Compras_Insumos_proveedor_id_fkey"


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
    bind = op.get_bind()
    if not _has_table("Compras_Insumos") or not _has_column("Compras_Insumos", "proveedor_id"):
        return
    if _has_table("maestros_proveedores"):
        # Orphans -> NULL (never delete rows).
        bind.execute(
            sa.text(
                'UPDATE "Compras_Insumos" SET proveedor_id = NULL '
                "WHERE proveedor_id IS NOT NULL AND NOT EXISTS "
                "(SELECT 1 FROM maestros_proveedores m "
                "WHERE m.id = \"Compras_Insumos\".proveedor_id)"
            )
        )
        if not _has_fk("Compras_Insumos", FK_NAME):
            op.create_foreign_key(
                FK_NAME,
                "Compras_Insumos",
                "maestros_proveedores",
                ["proveedor_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: the FK name is quoted — unquoted identifiers fold to lowercase
    # and IF EXISTS would silently miss "Compras_Insumos_proveedor_id_fkey".
    bind.execute(sa.text(f'ALTER TABLE "Compras_Insumos" DROP CONSTRAINT IF EXISTS "{FK_NAME}"'))
