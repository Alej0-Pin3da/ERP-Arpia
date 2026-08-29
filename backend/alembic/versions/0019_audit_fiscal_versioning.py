"""audit fiscal: precio_versions, costo_versions, cierres_mensuales"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0019_audit_fiscal_versioning"
down_revision: str | None = "0018_prendas_listas"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

def _has_table(table: str) -> bool:
    bind = op.get_bind()
    return table in sa.inspect(bind).get_table_names()

def upgrade() -> None:
    if not _has_table("precio_versions"):
        op.create_table("precio_versions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("producto_id", sa.Integer(), sa.ForeignKey("productos.id", ondelete="CASCADE"), nullable=False),
            sa.Column("variante_id", sa.Integer(), sa.ForeignKey("variantes_producto.id", ondelete="CASCADE"), nullable=True),
            sa.Column("precio", sa.Numeric(15,4), nullable=False),
            sa.Column("fecha_desde", sa.Date(), nullable=False),
            sa.Column("creado_por", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_precio_versions_producto_fecha", "precio_versions", ["producto_id", "fecha_desde"])
    if not _has_table("costo_versions"):
        op.create_table("costo_versions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("producto_id", sa.Integer(), sa.ForeignKey("productos.id", ondelete="CASCADE"), nullable=False),
            sa.Column("costo", sa.Numeric(15,4), nullable=False),
            sa.Column("fecha_desde", sa.Date(), nullable=False),
            sa.Column("creado_por", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_costo_versions_producto_fecha", "costo_versions", ["producto_id", "fecha_desde"])
    if not _has_table("cierres_mensuales"):
        op.create_table("cierres_mensuales",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("periodo", sa.String(7), nullable=False, unique=True),
            sa.Column("estado", sa.String(20), nullable=False, server_default="cerrado"),
            sa.Column("cerrado_por", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

def downgrade() -> None:
    for t in ["cierres_mensuales", "costo_versions", "precio_versions"]:
        if _has_table(t):
            op.drop_table(t)
