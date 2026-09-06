"""Provenance flags for hidratacion-datos-faltantes (F8 backfill).

- Productos.origen_precio / Insumos.origen_costo VARCHAR(20) NULL.
- NULL = pipeline value, 'backfill' = hydrated by backfill_precios_costos.py.
- Nullable + no data rewrite: backward compatible. Downgrade drops both.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028_backfill_provenance"
down_revision: str | None = "0027_audit_omisiones_indexes"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

COLUMNS = [("Productos", "origen_precio"), ("Insumos", "origen_costo")]


def _has_column(table: str, column: str) -> bool:
    try:
        return column in [c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)]
    except Exception:
        return False


def upgrade() -> None:
    for table, column in COLUMNS:
        if not _has_column(table, column):
            op.add_column(table, sa.Column(column, sa.String(20), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    for table, column in COLUMNS:
        try:
            bind.execute(sa.text(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS "{column}"'))
        except Exception:
            pass
