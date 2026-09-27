"""kits y kit_productos (V6 M1)

Revision ID: c84889c70b73
Revises: ddd8ad1b3d72
Create Date: 2026-09-27

Promotional boxes: Kits + Kit_Productos pivot (unique kit/product).
Costs are always computed on the fly (recursive BOM math) — nothing
stored, so kits never go stale.

NOTE: hand-written (autogenerate output stripped of unrelated index/table
noise — only Kits tables are touched here).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c84889c70b73'
down_revision: Union[str, None] = 'ddd8ad1b3d72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'Kits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('precio_promocional', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'Kit_Productos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kit_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.ForeignKeyConstraint(['kit_id'], ['Kits.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_id'], ['Productos.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kit_id', 'producto_id', name='uq_kit_productos_kit'),
    )
    op.create_index(op.f('ix_Kit_Productos_kit_id'), 'Kit_Productos', ['kit_id'], unique=False)
    op.create_index(
        op.f('ix_Kit_Productos_producto_id'), 'Kit_Productos', ['producto_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_Kit_Productos_producto_id'), table_name='Kit_Productos')
    op.drop_index(op.f('ix_Kit_Productos_kit_id'), table_name='Kit_Productos')
    op.drop_table('Kit_Productos')
    op.drop_table('Kits')
