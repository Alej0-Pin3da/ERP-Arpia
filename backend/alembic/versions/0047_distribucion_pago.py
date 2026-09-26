"""Pago por socia: fecha y comprobante en distribucion (0047).

El boton Registrar pago del acta no tenia donde persistir: agrega fecha_pago
(Date nullable) + comprobante (String 255 nullable) a liquidacion_distribucion.
Idempotente: columnas nuevas. Downgrade: las quita.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0047_distribucion_pago"
down_revision: str | None = "0046_ventas_liquidacion"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    try:
        op.add_column(
            "liquidacion_distribucion",
            sa.Column("fecha_pago", sa.Date(), nullable=True),
        )
    except Exception:
        pass
    try:
        op.add_column(
            "liquidacion_distribucion",
            sa.Column("comprobante", sa.String(255), nullable=True),
        )
    except Exception:
        pass


def downgrade() -> None:
    for col in ("comprobante", "fecha_pago"):
        try:
            op.drop_column("liquidacion_distribucion", col)
        except Exception:
            pass
