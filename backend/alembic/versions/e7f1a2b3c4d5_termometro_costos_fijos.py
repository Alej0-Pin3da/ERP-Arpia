"""termometro costos fijos mensuales (ParametrosCosteo.costos_fijos_mensuales)

Revision ID: e7f1a2b3c4d5
Revises: dcc928a70607
Create Date: 2026-09-29

Termómetro Operativo del Mes: monthly fixed operating costs live on the
costeo singleton so the break-even goal derives from real month sales.
Existing rows backfill to 0 (endpoint reports sin_configurar until set).

NOTE: hand-written (autogenerate output stripped of unrelated index/table
noise — only maestros_parametros_costeo is touched here).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e7f1a2b3c4d5'
down_revision: Union[str, None] = 'dcc928a70607'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'maestros_parametros_costeo',
        sa.Column(
            'costos_fijos_mensuales',
            sa.Numeric(precision=15, scale=4),
            server_default=sa.text("'0'::numeric"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('maestros_parametros_costeo', 'costos_fijos_mensuales')
