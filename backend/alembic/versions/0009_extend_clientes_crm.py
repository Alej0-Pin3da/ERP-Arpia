"""extend Clientes with CRM fields

Revision ID: 0009_extend_clientes_crm
Revises: 20260821_wac
Create Date: 2026-08-23

CRM-1: 10 nullable cols + ix_clientes_tipo/ciudad
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_extend_clientes_crm"
down_revision: str | None = "20260821_wac"
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
    # 10 nullable cols — idempotent guards for re-run safety
    if not _has_column("Clientes", "ciudad"):
        op.add_column("Clientes", sa.Column("ciudad", sa.String(length=80), nullable=True))
    if not _has_column("Clientes", "direccion"):
        op.add_column("Clientes", sa.Column("direccion", sa.String(length=200), nullable=True))
    if not _has_column("Clientes", "tipo"):
        op.add_column("Clientes", sa.Column("tipo", sa.String(length=30), nullable=True))
    if not _has_column("Clientes", "talla_habitual"):
        op.add_column("Clientes", sa.Column("talla_habitual", sa.String(length=10), nullable=True))
    if not _has_column("Clientes", "talla_superior"):
        op.add_column("Clientes", sa.Column("talla_superior", sa.String(length=10), nullable=True))
    if not _has_column("Clientes", "talla_inferior"):
        op.add_column("Clientes", sa.Column("talla_inferior", sa.String(length=10), nullable=True))
    if not _has_column("Clientes", "categoria_preferida"):
        op.add_column("Clientes", sa.Column("categoria_preferida", sa.String(length=50), nullable=True))
    if not _has_column("Clientes", "tipo_producto_frecuente"):
        op.add_column(
            "Clientes", sa.Column("tipo_producto_frecuente", sa.String(length=50), nullable=True)
        )
    if not _has_column("Clientes", "notas"):
        op.add_column("Clientes", sa.Column("notas", sa.Text(), nullable=True))
    if not _has_column("Clientes", "medidas"):
        op.add_column("Clientes", sa.Column("medidas", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Indices for filtering — exact names required by spec
    if not _has_index("Clientes", "ix_clientes_tipo"):
        op.create_index("ix_clientes_tipo", "Clientes", ["tipo"], unique=False)
    if not _has_index("Clientes", "ix_clientes_ciudad"):
        op.create_index("ix_clientes_ciudad", "Clientes", ["ciudad"], unique=False)


def downgrade() -> None:
    # Drop indices first
    if _has_index("Clientes", "ix_clientes_ciudad"):
        try:
            op.drop_index("ix_clientes_ciudad", table_name="Clientes")
        except Exception:
            pass
    if _has_index("Clientes", "ix_clientes_tipo"):
        try:
            op.drop_index("ix_clientes_tipo", table_name="Clientes")
        except Exception:
            pass
    # Drop columns reverse order
    for col in [
        "medidas",
        "notas",
        "tipo_producto_frecuente",
        "categoria_preferida",
        "talla_inferior",
        "talla_superior",
        "talla_habitual",
        "tipo",
        "direccion",
        "ciudad",
    ]:
        if _has_column("Clientes", col):
            op.drop_column("Clientes", col)
