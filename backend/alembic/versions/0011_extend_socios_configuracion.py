"""extend Socios with 10 nullable cols + ix_socios_rol/activo

Revision ID: 0011_extend_socios_configuracion
Revises: 0010_ventas_canal_pago
Create Date: 2026-08-24
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0011_extend_socios_configuracion"
down_revision: str | None = "0010_ventas_canal_pago"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def _has_column(t: str, c: str) -> bool:
    try: return c in [x["name"] for x in sa.inspect(op.get_bind()).get_columns(t)]
    except Exception: return False
def _has_index(t: str, n: str) -> bool:
    try: return n in [i["name"] for i in sa.inspect(op.get_bind()).get_indexes(t)]
    except Exception: return False

def upgrade() -> None:
    if not _has_column("Socios_Configuracion", "rol"): op.add_column("Socios_Configuracion", sa.Column("rol", sa.String(50), nullable=True))
    if not _has_column("Socios_Configuracion", "banco"): op.add_column("Socios_Configuracion", sa.Column("banco", sa.String(100), nullable=True))
    if not _has_column("Socios_Configuracion", "es_fondo_taller"): op.add_column("Socios_Configuracion", sa.Column("es_fondo_taller", sa.Boolean(), nullable=True, server_default=sa.text("false")))
    if not _has_column("Socios_Configuracion", "telefono"): op.add_column("Socios_Configuracion", sa.Column("telefono", sa.String(50), nullable=True))
    if not _has_column("Socios_Configuracion", "email"): op.add_column("Socios_Configuracion", sa.Column("email", sa.String(255), nullable=True))
    if not _has_column("Socios_Configuracion", "tipo_cuenta"): op.add_column("Socios_Configuracion", sa.Column("tipo_cuenta", sa.String(50), nullable=True))
    if not _has_column("Socios_Configuracion", "numero_cuenta"): op.add_column("Socios_Configuracion", sa.Column("numero_cuenta", sa.String(50), nullable=True))
    if not _has_column("Socios_Configuracion", "titular_cuenta"): op.add_column("Socios_Configuracion", sa.Column("titular_cuenta", sa.String(150), nullable=True))
    if not _has_column("Socios_Configuracion", "activo"): op.add_column("Socios_Configuracion", sa.Column("activo", sa.Boolean(), nullable=True, server_default=sa.text("true")))
    if not _has_column("Socios_Configuracion", "notas"): op.add_column("Socios_Configuracion", sa.Column("notas", sa.Text(), nullable=True))
    if not _has_index("Socios_Configuracion", "ix_socios_rol"): op.create_index("ix_socios_rol", "Socios_Configuracion", ["rol"])
    if not _has_index("Socios_Configuracion", "ix_socios_activo"): op.create_index("ix_socios_activo", "Socios_Configuracion", ["activo"])

def downgrade() -> None:
    for idx in ["ix_socios_activo", "ix_socios_rol"]:
        if _has_index("Socios_Configuracion", idx):
            try: op.drop_index(idx, table_name="Socios_Configuracion")
            except Exception: pass
    for col in ["notas","activo","titular_cuenta","numero_cuenta","tipo_cuenta","email","telefono","es_fondo_taller","banco","rol"]:
        if _has_column("Socios_Configuracion", col): op.drop_column("Socios_Configuracion", col)
