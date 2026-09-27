"""webhook eventos (V6 M3)

Revision ID: 557107cefd09
Revises: 2a60aa143124
Create Date: 2026-09-27

Inbound webhook receipts (idempotency guard per external event).

Also backfills ``ix_Reparto_Ventas_venta_id``: the hand-written M2
migration named the unique constraint explicitly, so autogenerate never
emitted the model's plain ``index=True`` — added here to converge
DB and models.

NOTE: hand-written (autogenerate output stripped of unrelated index/table
noise — only Webhook/Reparto objects are touched here).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '557107cefd09'
down_revision: Union[str, None] = '2a60aa143124'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'Webhook_Eventos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('venta_id', sa.Integer(), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column(
            'creado_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['venta_id'], ['Ventas.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'source', 'external_id', name='uq_webhook_eventos_source_ext'
        ),
    )
    op.create_index(
        op.f('ix_Webhook_Eventos_external_id'),
        'Webhook_Eventos',
        ['external_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_Reparto_Ventas_venta_id'), 'Reparto_Ventas', ['venta_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_Reparto_Ventas_venta_id'), table_name='Reparto_Ventas')
    op.drop_index(op.f('ix_Webhook_Eventos_external_id'), table_name='Webhook_Eventos')
    op.drop_table('Webhook_Eventos')
