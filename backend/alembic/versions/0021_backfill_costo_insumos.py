"""backfill costo_insumos from costos_operativos_fijos where null"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021_backfill_costo_insumos"
down_revision: str | None = "0020_productos_cabecera"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    # Backfill costo_insumos where it's NULL and we have a total to derive from
    # costo_insumos = GREATEST(costos_operativos_fijos - COALESCE(mano_obra,0) - COALESCE(cif_energia,0), 0)
    # Only for rows where costo_insumos IS NULL and costos_operativos_fijos > 0
    conn.execute(
        sa.text(
            """
            UPDATE "Productos"
            SET costo_insumos = GREATEST(
                COALESCE(costos_operativos_fijos, 0) - COALESCE(mano_obra, 0) - COALESCE(cif_energia, 0),
                0
            )
            WHERE costo_insumos IS NULL
              AND COALESCE(costos_operativos_fijos, 0) > 0
            """
        )
    )


def downgrade() -> None:
    # No reverse for backfill (data migration); set back to NULL where we set it.
    # We keep it as-is on downgrade (no-op) to avoid data loss.
    pass
