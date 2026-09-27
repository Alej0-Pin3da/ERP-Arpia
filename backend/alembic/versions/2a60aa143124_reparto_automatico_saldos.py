"""reparto automatico saldos (V6 M2)

Revision ID: 2a60aa143124
Revises: c84889c70b73
Create Date: 2026-09-27

Automatic profit split: Reglas_Liquidacion (split rules), Saldos_Socias
(running balances), Reparto_Ventas (per-sale audit ledger). Rules are
seeded from the current statute (active Socios_Configuracion rows) so the
split works out of the box; with no rules, sales simply skip the split.

NOTE: hand-written (autogenerate output stripped of unrelated index/table
noise — only Reparto tables are touched here).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2a60aa143124'
down_revision: Union[str, None] = 'c84889c70b73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_SEED_REGLAS_DESDE_ESTATUTO = """
INSERT INTO "Reglas_Liquidacion" (cuenta_destino, porcentaje, activo)
SELECT nombre, porcentaje_participacion, TRUE FROM "Socios_Configuracion"
WHERE activo IS TRUE
ON CONFLICT (cuenta_destino) DO NOTHING
"""


def upgrade() -> None:
    op.create_table(
        'Reglas_Liquidacion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cuenta_destino', sa.String(length=100), nullable=False),
        sa.Column('porcentaje', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cuenta_destino', name='uq_reglas_liquidacion_cuenta'),
    )
    op.create_table(
        'Saldos_Socias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cuenta', sa.String(length=100), nullable=False),
        sa.Column('saldo', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column(
            'actualizado_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cuenta', name='uq_saldos_socias_cuenta'),
    )
    op.create_index(op.f('ix_Saldos_Socias_cuenta'), 'Saldos_Socias', ['cuenta'], unique=False)
    op.create_table(
        'Reparto_Ventas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venta_id', sa.Integer(), nullable=False),
        sa.Column('cuenta', sa.String(length=100), nullable=False),
        sa.Column('monto', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.ForeignKeyConstraint(['venta_id'], ['Ventas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('venta_id', 'cuenta', name='uq_reparto_ventas_venta_cuenta'),
    )
    # Seed from the statute: active socias become the initial split rules.
    op.execute(sa.text(_SEED_REGLAS_DESDE_ESTATUTO))


def downgrade() -> None:
    op.drop_table('Reparto_Ventas')
    op.drop_table('Saldos_Socias')
    op.drop_table('Reglas_Liquidacion')
