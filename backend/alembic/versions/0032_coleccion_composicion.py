"""Etiqueta de Autor: Productos.coleccion + Productos.composicion.

- `Productos.coleccion` VARCHAR(150) NULL: nombre de colección imprimible
  en la etiqueta (default de UI "Colección Eterna", antes hardcodeado).
- `Productos.composicion` VARCHAR(255) NULL: composición textil imprimible
  (antes siempre '—', nada la almacenaba).

Idempotent guards (style 0014/0022/0024/0030/0031): exact column probing,
never CAST(:table AS regclass). Downgrade drops both columns.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0032_coleccion_composicion"
down_revision: str | None = "0031_tiempos_fase_energia"
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
    if _has_table("Productos"):
        if not _has_column("Productos", "coleccion"):
            op.add_column(
                "Productos",
                sa.Column("coleccion", sa.String(150), nullable=True),
            )
        if not _has_column("Productos", "composicion"):
            op.add_column(
                "Productos",
                sa.Column("composicion", sa.String(255), nullable=True),
            )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text('ALTER TABLE "Productos" DROP COLUMN IF EXISTS "composicion"'))
    bind.execute(sa.text('ALTER TABLE "Productos" DROP COLUMN IF EXISTS "coleccion"'))
