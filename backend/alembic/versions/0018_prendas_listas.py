"""create prendas_confeccionadas table

Revision ID: 0018_prendas_listas
Revises: 0017_pedidos_produccion
Create Date: 2026-08-27

Fase 4: Prendas confeccionadas (stock de producto terminado para venta)
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018_prendas_listas"
down_revision: str | None = "0017_pedidos_produccion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table in insp.get_table_names()


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return index_name in [i["name"] for i in insp.get_indexes(table)]


def upgrade() -> None:
    if not _has_table("prendas_confeccionadas"):
        op.create_table(
            "prendas_confeccionadas",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("variante_id", sa.Integer(), nullable=False),
            sa.Column("talla", sa.String(length=20), nullable=True),
            sa.Column("estado", sa.String(length=30), nullable=False, server_default="disponible"),
            sa.Column("ubicacion", sa.String(length=100), nullable=True),
            sa.Column("costo_real", sa.Numeric(precision=15, scale=4), nullable=True),
            sa.Column("precio_venta", sa.Numeric(precision=15, scale=4), nullable=True),
            sa.Column("fecha_confeccion", sa.Date(), nullable=True),
            sa.Column("pedido_id", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["variante_id"], ["Variantes_Producto.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_produccion.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

    if _has_table("prendas_confeccionadas"):
        if not _has_index("prendas_confeccionadas", "ix_prendas_variante_estado"):
            op.create_index(
                "ix_prendas_variante_estado", "prendas_confeccionadas", ["variante_id", "estado"]
            )
        if not _has_index("prendas_confeccionadas", "ix_prendas_pedido_id"):
            op.create_index("ix_prendas_pedido_id", "prendas_confeccionadas", ["pedido_id"])


def downgrade() -> None:
    if _has_table("prendas_confeccionadas"):
        if _has_index("prendas_confeccionadas", "ix_prendas_pedido_id"):
            op.drop_index("ix_prendas_pedido_id", table_name="prendas_confeccionadas")
        if _has_index("prendas_confeccionadas", "ix_prendas_variante_estado"):
            op.drop_index("ix_prendas_variante_estado", table_name="prendas_confeccionadas")
        op.drop_table("prendas_confeccionadas")
