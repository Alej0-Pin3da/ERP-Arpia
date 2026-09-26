"""Link ventas a su liquidacion (0046).

Una venta pertenece a lo sumo a una liquidacion: al crearla con venta_ids se
marca cada venta (solo confirmed y sin liquidar). Borrar la liquidacion libera
las ventas (SET NULL) en vez de bloquear. Idempotente: columna nullable nueva.
Downgrade: quita la columna (se pierde el link, no las ventas).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0046_ventas_liquidacion"
down_revision: str | None = "0045_cotizaciones_hilos"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    try:
        op.add_column(
            "Ventas",
            sa.Column("liquidacion_id", sa.Integer(), nullable=True),
        )
    except Exception:
        pass
    try:
        op.create_foreign_key(
            "fk_ventas_liquidacion",
            "Ventas",
            "liquidaciones",
            ["liquidacion_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        pass
    try:
        op.create_index("ix_ventas_liquidacion", "Ventas", ["liquidacion_id"])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index("ix_ventas_liquidacion", table_name="Ventas")
    except Exception:
        pass
    try:
        op.drop_constraint("fk_ventas_liquidacion", "Ventas", type_="foreignkey")
    except Exception:
        pass
    try:
        op.drop_column("Ventas", "liquidacion_id")
    except Exception:
        pass
