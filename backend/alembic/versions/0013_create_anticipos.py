"""create anticipos with checks and partial unique

Revision ID: 0013_create_anticipos
Revises: 0012_create_liquidaciones
Create Date: 2026-08-24
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0013_create_anticipos"
down_revision: str | None = "0012_create_liquidaciones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def _has_table(t: str) -> bool: return t in sa.inspect(op.get_bind()).get_table_names()
def _has_index(t: str, n: str) -> bool:
    try: return n in [i["name"] for i in sa.inspect(op.get_bind()).get_indexes(t)]
    except Exception: return False

def upgrade() -> None:
    if not _has_table("anticipos"):
        op.create_table("anticipos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("socia_id", sa.Integer(), sa.ForeignKey("Socios_Configuracion.id", ondelete="CASCADE"), nullable=False),
            sa.Column("liquidacion_id", sa.Integer(), sa.ForeignKey("liquidaciones.id", ondelete="SET NULL"), nullable=True),
            sa.Column("monto", sa.Numeric(12,2), nullable=False),
            sa.Column("fecha", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
            sa.Column("estado", sa.String(20), nullable=False, server_default=sa.text("'PENDIENTE_DESCUENTO'")),
            sa.Column("concepto", sa.String(255), nullable=True),
            sa.Column("metodo_desembolso", sa.String(50), nullable=True),
            sa.Column("comprobante", sa.String(255), nullable=True),
            sa.Column("observaciones", sa.Text(), nullable=True),
            sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("monto > 0", name="ck_anticipos_monto_positivo"),
            sa.CheckConstraint("estado IN ('PENDIENTE_DESCUENTO','DESCONTADO','ANULADO')", name="ck_anticipos_estado"),
        )
        op.create_index("ix_anticipos_socia_fecha","anticipos",["socia_id","fecha"])
        op.create_index("ix_anticipos_estado","anticipos",["estado"])
        op.create_index("ix_anticipos_liquidacion_id","anticipos",["liquidacion_id"])
        op.execute("CREATE UNIQUE INDEX ix_anticipos_socia_liquidacion ON anticipos (socia_id,liquidacion_id) WHERE liquidacion_id IS NOT NULL")
    else:
        if not _has_index("anticipos","ix_anticipos_socia_fecha"): op.create_index("ix_anticipos_socia_fecha","anticipos",["socia_id","fecha"])
        if not _has_index("anticipos","ix_anticipos_socia_liquidacion"):
            try: op.execute("CREATE UNIQUE INDEX ix_anticipos_socia_liquidacion ON anticipos (socia_id,liquidacion_id) WHERE liquidacion_id IS NOT NULL")
            except Exception: pass

def downgrade() -> None:
    if _has_table("anticipos"):
        try: op.execute("DROP INDEX IF EXISTS ix_anticipos_socia_liquidacion")
        except Exception: pass
        op.drop_table("anticipos")
