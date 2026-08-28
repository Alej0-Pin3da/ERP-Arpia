"""create pedidos_produccion table

Revision ID: 0017_pedidos_produccion
Revises: 0016_insumos_bom
Create Date: 2026-08-27

Fase 4: Pedidos de producción (órdenes de confección en taller)
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017_pedidos_produccion"
down_revision: str | None = "0016_insumos_bom"
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
    if not _has_table("pedidos_produccion"):
        op.create_table(
            "pedidos_produccion",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("producto_id", sa.Integer(), nullable=False),
            sa.Column("variante_id", sa.Integer(), nullable=True),
            sa.Column("cantidad", sa.Integer(), nullable=False),
            sa.Column("cantidad_producida", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("estado", sa.String(length=30), nullable=False, server_default="pendiente"),
            sa.Column("prioridad", sa.String(length=20), nullable=False, server_default="normal"),
            sa.Column("fecha_pedido", sa.Date(), nullable=False, server_default=sa.func.current_date()),
            sa.Column("fecha_entrega_estimada", sa.Date(), nullable=True),
            sa.Column("observaciones", sa.Text(), nullable=True),
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
            sa.ForeignKeyConstraint(["producto_id"], ["Productos.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["variante_id"], ["Variantes_Producto.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

    if _has_table("pedidos_produccion"):
        if not _has_index("pedidos_produccion", "ix_pedidos_producto_id"):
            op.create_index("ix_pedidos_producto_id", "pedidos_produccion", ["producto_id"])
        if not _has_index("pedidos_produccion", "ix_pedidos_estado_prioridad"):
            op.create_index("ix_pedidos_estado_prioridad", "pedidos_produccion", ["estado", "prioridad"])


def downgrade() -> None:
    if _has_table("pedidos_produccion"):
        if _has_index("pedidos_produccion", "ix_pedidos_estado_prioridad"):
            op.drop_index("ix_pedidos_estado_prioridad", table_name="pedidos_produccion")
        if _has_index("pedidos_produccion", "ix_pedidos_producto_id"):
            op.drop_index("ix_pedidos_producto_id", table_name="pedidos_produccion")
        op.drop_table("pedidos_produccion")
