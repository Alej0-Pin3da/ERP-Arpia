"""cotizaciones BOM dinamico JSONB

Revision ID: ddd8ad1b3d72
Revises: 0047_distribucion_pago
Create Date: 2026-09-27

Dynamic BOM for quotes: adds ``insumos_detalle`` (JSONB snapshot, immutable
per quote) and drops the static tela/forro columns plus the global
``desperdicio_pct`` (waste is now per line). Pre-existing rows are snapshotted
into the JSONB *before* the drop so no history is lost.

NOTE: hand-written (autogenerate output stripped of unrelated index/table
noise — only Cotizaciones is touched here).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ddd8ad1b3d72'
down_revision: Union[str, None] = '0047_distribucion_pago'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_SNAPSHOT_TELA_FORRO = """
UPDATE "Cotizaciones" SET insumos_detalle = sub.items
FROM (
  SELECT id, jsonb_agg(elem ORDER BY ord) AS items FROM (
    SELECT id, 1 AS ord, jsonb_build_object(
      'nombre', 'Tela principal',
      'cantidad', metros_tela,
      'precio_unitario', precio_metro_tela,
      'unidad_medida', 'm',
      'desperdicio_pct', desperdicio_pct
    ) AS elem FROM "Cotizaciones"
    WHERE COALESCE(metros_tela, 0) <> 0 OR COALESCE(precio_metro_tela, 0) <> 0
    UNION ALL
    SELECT id, 2 AS ord, jsonb_build_object(
      'nombre', 'Forro',
      'cantidad', metros_forro,
      'precio_unitario', precio_metro_forro,
      'unidad_medida', 'm',
      'desperdicio_pct', desperdicio_pct
    ) AS elem FROM "Cotizaciones"
    WHERE COALESCE(metros_forro, 0) <> 0 OR COALESCE(precio_metro_forro, 0) <> 0
  ) u GROUP BY id
) sub WHERE "Cotizaciones".id = sub.id
"""


def upgrade() -> None:
    op.add_column(
        'Cotizaciones',
        sa.Column(
            'insumos_detalle',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='[]',
            nullable=True,
        ),
    )
    # Preserve history: snapshot static tela/forro into the JSONB first.
    op.execute(sa.text(_SNAPSHOT_TELA_FORRO))
    # Rows with no tela/forro keep the empty-list default (never NULL).
    op.execute(sa.text("UPDATE \"Cotizaciones\" SET insumos_detalle = '[]' WHERE insumos_detalle IS NULL"))
    op.drop_column('Cotizaciones', 'metros_tela')
    op.drop_column('Cotizaciones', 'precio_metro_tela')
    op.drop_column('Cotizaciones', 'metros_forro')
    op.drop_column('Cotizaciones', 'precio_metro_forro')
    op.drop_column('Cotizaciones', 'desperdicio_pct')


def downgrade() -> None:
    op.add_column(
        'Cotizaciones',
        sa.Column(
            'metros_tela',
            sa.NUMERIC(precision=15, scale=4),
            server_default=sa.text("'0'::numeric"),
            nullable=False,
        ),
    )
    op.add_column(
        'Cotizaciones',
        sa.Column(
            'precio_metro_tela',
            sa.NUMERIC(precision=15, scale=4),
            server_default=sa.text("'0'::numeric"),
            nullable=False,
        ),
    )
    op.add_column(
        'Cotizaciones',
        sa.Column(
            'metros_forro',
            sa.NUMERIC(precision=15, scale=4),
            server_default=sa.text("'0'::numeric"),
            nullable=False,
        ),
    )
    op.add_column(
        'Cotizaciones',
        sa.Column(
            'precio_metro_forro',
            sa.NUMERIC(precision=15, scale=4),
            server_default=sa.text("'0'::numeric"),
            nullable=False,
        ),
    )
    op.add_column(
        'Cotizaciones',
        sa.Column(
            'desperdicio_pct',
            sa.NUMERIC(precision=15, scale=4),
            server_default=sa.text("'0'::numeric"),
            nullable=False,
        ),
    )
    op.drop_column('Cotizaciones', 'insumos_detalle')
