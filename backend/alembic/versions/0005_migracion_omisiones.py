"""migracion omisiones

Revision ID: d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9
Revises: a4f3c9d2b8e14f6a9c5e5b7d1a1a8e3c
Create Date: 2026-08-09 12:30:00.000000

Additive change (MIG-1): new Migracion_Omisiones table populated by the
migration CLI in commit mode. Downgrade drops only this table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9'
down_revision: Union[str, None] = 'a4f3c9d2b8e14f6a9c5e5b7d1a1a8e3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'Migracion_Omisiones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('corrida_id', sa.String(length=40), nullable=True),
        sa.Column('fecha_corrida', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('fase', sa.String(length=20), nullable=True),
        sa.Column('hoja', sa.String(length=64), nullable=True),
        sa.Column('fila', sa.Integer(), nullable=True),
        sa.Column('celda', sa.String(length=16), nullable=True),
        sa.Column('nivel', sa.String(length=8), nullable=False),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('resuelta', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("nivel IN ('WARN', 'ERROR')", name='ck_migracion_omisiones_nivel'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('Migracion_Omisiones')
