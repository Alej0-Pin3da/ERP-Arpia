"""Direct product link on finished garments (0040).

- `prendas_confeccionadas.producto_id` INTEGER NULL FK Productos.id
  ON DELETE SET NULL: generic (talla-less) garments attribute to a product
  (e.g. Tote Bag) instead of falling into an anonymous "Sin producto" group.
  Variant-linked rows keep resolving through their variant; producto_id is
  the explicit override and the only attribution for generic rows.
- Nullable + no backfill here (existing generic rows are re-attributed by a
  separate stated-assumption script, never inferred in a migration).

Idempotent guards: exact column probing, never CAST(:table AS regclass).
Downgrade drops the column (FK goes with it).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0040_prenda_producto"
down_revision: str | None = "0039_venta_descuento_motivo"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "prendas_confeccionadas"
COLUMN = "producto_id"


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
            sa.ForeignKey("Productos.id", ondelete="SET NULL"),
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
