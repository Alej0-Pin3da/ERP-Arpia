"""create liquidaciones header + distribucion child

Revision ID: 0012_create_liquidaciones
Revises: 0011_extend_socios_configuracion
Create Date: 2026-08-24
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0012_create_liquidaciones"
down_revision: str | None = "0011_extend_socios_configuracion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def _has_table(t: str) -> bool: return t in sa.inspect(op.get_bind()).get_table_names()

def upgrade() -> None:
    if not _has_table("liquidaciones"):
        op.create_table("liquidaciones",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("codigo", sa.String(12), nullable=False, unique=True),
            sa.Column("periodo", sa.String(20), nullable=False),
            sa.Column("fecha_cierre", sa.Date(), nullable=False),
            sa.Column("total_ventas_brutas", sa.Numeric(12,2), nullable=False),
            sa.Column("costo_taller_insumos", sa.Numeric(12,2), nullable=False),
            sa.Column("gastos_operativos", sa.Numeric(12,2), nullable=False),
            sa.Column("utilidad_neta_total", sa.Numeric(12,2), nullable=False),
            sa.Column("fondo_reinversion_monto", sa.Numeric(12,2), nullable=False),
            sa.Column("utilidad_repartible", sa.Numeric(12,2), nullable=False),
            sa.Column("estado", sa.String(20), nullable=False, server_default=sa.text("'BORRADOR'")),
            sa.Column("observaciones", sa.Text(), nullable=True),
            sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("estado IN ('BORRADOR','APROBADA','PAGADA')", name="ck_liquidaciones_estado"),
            sa.UniqueConstraint("codigo", name="uq_liquidaciones_codigo"),
        )
        op.create_index("ix_liquidaciones_periodo","liquidaciones",["periodo"])
        op.create_index("ix_liquidaciones_estado","liquidaciones",["estado"])
        op.create_index("ix_liquidaciones_codigo","liquidaciones",["codigo"])
    if not _has_table("liquidacion_distribucion"):
        op.create_table("liquidacion_distribucion",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("liquidacion_id", sa.Integer(), sa.ForeignKey("liquidaciones.id", ondelete="CASCADE"), nullable=False),
            sa.Column("socia_id", sa.Integer(), sa.ForeignKey("Socios_Configuracion.id", ondelete="CASCADE"), nullable=False),
            sa.Column("porcentaje", sa.Numeric(5,2), nullable=False),
            sa.Column("monto_bruto", sa.Numeric(12,2), nullable=False),
            sa.Column("deduccion_anticipos", sa.Numeric(12,2), nullable=False, server_default=sa.text("0")),
            sa.Column("monto_neto", sa.Numeric(12,2), nullable=False),
            sa.Column("estado_pago", sa.String(20), nullable=False, server_default=sa.text("'PENDIENTE'")),
            sa.CheckConstraint("estado_pago IN ('PENDIENTE','PAGADO','RETENIDO')", name="ck_distribucion_estado_pago"),
            sa.UniqueConstraint("liquidacion_id","socia_id", name="uq_distribucion_liquidacion_socia"),
        )
        op.create_index("ix_distribucion_liquidacion_id","liquidacion_distribucion",["liquidacion_id"])
        op.create_index("ix_distribucion_socia_id","liquidacion_distribucion",["socia_id"])

def downgrade() -> None:
    if _has_table("liquidacion_distribucion"): op.drop_table("liquidacion_distribucion")
    if _has_table("liquidaciones"): op.drop_table("liquidaciones")
