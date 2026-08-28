"""extend insumos and bom tables

Revision ID: 0016_insumos_bom
Revises: 0015_maestros_tallas
Create Date: 2026-08-27

Fase 4: Insumos (codigo, descripcion, tipo, ubicacion) + BOM (fases, tiempo_estimado_minutos, markup_porcentual)
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0016_insumos_bom"
down_revision: str | None = "0015_maestros_tallas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column in [c["name"] for c in insp.get_columns(table)]


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return index_name in [i["name"] for i in insp.get_indexes(table)]


def upgrade() -> None:
    # 1. Insumos additions
    if not _has_column("Insumos", "codigo"):
        op.add_column("Insumos", sa.Column("codigo", sa.String(length=50), nullable=True))
    if not _has_column("Insumos", "descripcion"):
        op.add_column("Insumos", sa.Column("descripcion", sa.Text(), nullable=True))
    if not _has_column("Insumos", "tipo"):
        op.add_column("Insumos", sa.Column("tipo", sa.String(length=50), nullable=True))
    if not _has_column("Insumos", "ubicacion"):
        op.add_column("Insumos", sa.Column("ubicacion", sa.String(length=100), nullable=True))

    if not _has_index("Insumos", "ix_insumos_codigo"):
        op.create_index("ix_insumos_codigo", "Insumos", ["codigo"])
    if not _has_index("Insumos", "ix_insumos_tipo"):
        op.create_index("ix_insumos_tipo", "Insumos", ["tipo"])

    # 2. BOM_Insumos additions
    if not _has_column("BOM_Insumos", "fases"):
        op.add_column(
            "BOM_Insumos",
            sa.Column("fases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if not _has_column("BOM_Insumos", "tiempo_estimado_minutos"):
        op.add_column(
            "BOM_Insumos",
            sa.Column("tiempo_estimado_minutos", sa.Integer(), nullable=True),
        )
    if not _has_column("BOM_Insumos", "markup_porcentual"):
        op.add_column(
            "BOM_Insumos",
            sa.Column("markup_porcentual", sa.Numeric(precision=15, scale=4), nullable=True),
        )

    # 3. BOM_Productos additions
    if not _has_column("BOM_Productos", "fases"):
        op.add_column(
            "BOM_Productos",
            sa.Column("fases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if not _has_column("BOM_Productos", "tiempo_estimado_minutos"):
        op.add_column(
            "BOM_Productos",
            sa.Column("tiempo_estimado_minutos", sa.Integer(), nullable=True),
        )
    if not _has_column("BOM_Productos", "markup_porcentual"):
        op.add_column(
            "BOM_Productos",
            sa.Column("markup_porcentual", sa.Numeric(precision=15, scale=4), nullable=True),
        )


def downgrade() -> None:
    # BOM_Productos
    if _has_column("BOM_Productos", "markup_porcentual"):
        op.drop_column("BOM_Productos", "markup_porcentual")
    if _has_column("BOM_Productos", "tiempo_estimado_minutos"):
        op.drop_column("BOM_Productos", "tiempo_estimado_minutos")
    if _has_column("BOM_Productos", "fases"):
        op.drop_column("BOM_Productos", "fases")

    # BOM_Insumos
    if _has_column("BOM_Insumos", "markup_porcentual"):
        op.drop_column("BOM_Insumos", "markup_porcentual")
    if _has_column("BOM_Insumos", "tiempo_estimado_minutos"):
        op.drop_column("BOM_Insumos", "tiempo_estimado_minutos")
    if _has_column("BOM_Insumos", "fases"):
        op.drop_column("BOM_Insumos", "fases")

    # Insumos
    if _has_index("Insumos", "ix_insumos_tipo"):
        op.drop_index("ix_insumos_tipo", table_name="Insumos")
    if _has_index("Insumos", "ix_insumos_codigo"):
        op.drop_index("ix_insumos_codigo", table_name="Insumos")
    if _has_column("Insumos", "ubicacion"):
        op.drop_column("Insumos", "ubicacion")
    if _has_column("Insumos", "tipo"):
        op.drop_column("Insumos", "tipo")
    if _has_column("Insumos", "descripcion"):
        op.drop_column("Insumos", "descripcion")
    if _has_column("Insumos", "codigo"):
        op.drop_column("Insumos", "codigo")
