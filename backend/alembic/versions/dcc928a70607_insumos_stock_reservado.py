"""insumos stock_reservado (V6 M4)

Revision ID: dcc928a70607
Revises: 557107cefd09
Create Date: 2026-09-27

Predictive reservations: open production orders set aside their BOM
explosion here (see services/reservas.py). Existing rows backfill to 0.

NOTE: hand-written (autogenerate output stripped of unrelated index/table
noise — only Insumos.stock_reservado is touched here).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'dcc928a70607'
down_revision: Union[str, None] = '557107cefd09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'Insumos',
        sa.Column(
            'stock_reservado',
            sa.Numeric(precision=15, scale=4),
            server_default=sa.text("'0'::numeric"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('Insumos', 'stock_reservado')
