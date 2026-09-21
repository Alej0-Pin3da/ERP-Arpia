"""Discount code + reason on sales (0039).

- `Ventas.codigo_descuento` VARCHAR(50) NULL: bono/código aplicado (tal cual).
- `Ventas.motivo_descuento` VARCHAR(30) NULL + CHECK
  ('bono','aniversario','lanzamiento','rotacion','otro'): por qué se
  descuenta (rotación de colección anterior, aniversario, etc.).
- Historical rows keep NULLs (no backfill: old CSV notes were free text).

Idempotent guards: exact column/check probing, never CAST(:table AS
regclass). Downgrade drops the check then the columns.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039_venta_descuento_motivo"
down_revision: str | None = "0038_prenda_exhibicion"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "Ventas"
CHECK = "ck_ventas_motivo_descuento"
COLUMNS = ("codigo_descuento", "motivo_descuento")


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
    if not _has_column(TABLE, "codigo_descuento"):
        op.add_column(TABLE, sa.Column("codigo_descuento", sa.String(50), nullable=True))
    if not _has_column(TABLE, "motivo_descuento"):
        op.add_column(TABLE, sa.Column("motivo_descuento", sa.String(30), nullable=True))
    if not _has_check(TABLE, CHECK):
        op.create_check_constraint(
            CHECK,
            TABLE,
            "motivo_descuento IS NULL OR motivo_descuento IN "
            "('bono','aniversario','lanzamiento','rotacion','otro')",
        )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP CONSTRAINT IF EXISTS "{CHECK}"'))
    for column in COLUMNS:
        bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP COLUMN IF EXISTS "{column}"'))
