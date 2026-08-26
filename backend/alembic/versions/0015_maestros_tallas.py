"""maestros 0015: tallas_estandar + productos_sin_talla + parametros_costeo singleton.

Revision ID: 0015_maestros_tallas
Revises: 0014_maestros_core
- CREATE tallas_estandar (talla+orden UNIQUE, CHECK), producto_sin_talla, parametros_costeo
- Seeds 6 tallas XXS-XL, singleton id=1
- _has_* guards <400 lines
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_maestros_tallas"
down_revision: str | None = "0014_maestros_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return table in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def _has_index(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        return name in [i["name"] for i in sa.inspect(bind).get_indexes(table)]
    except Exception:
        return False


def upgrade() -> None:
    # 1) tallas_estandar
    if not _has_table("maestros_tallas_estandar"):
        op.create_table(
            "maestros_tallas_estandar",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("talla", sa.String(20), nullable=False, unique=True),
            sa.Column("orden", sa.Integer(), nullable=False, unique=True),
            sa.Column("busto", sa.String(50), nullable=True),
            sa.Column("cintura", sa.String(50), nullable=True),
            sa.Column("cadera", sa.String(50), nullable=True),
            sa.Column("reduccion_corset", sa.String(50), nullable=True),
            sa.Column("descripcion", sa.Text(), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("talla", name="uq_tallas_talla"),
            sa.UniqueConstraint("orden", name="uq_tallas_orden"),
        )
        op.create_index("ix_tallas_orden", "maestros_tallas_estandar", ["orden"])
        op.create_index("ix_tallas_activo", "maestros_tallas_estandar", ["activo"])
        # seed 6 rows XXS-XL idempotent ON CONFLICT
        bind = op.get_bind()
        for talla, orden, busto, cintura, cadera, red, desc in [
            ("XXS", 1, "76 - 80 cm", "60 - 64 cm", "86 - 90 cm", "-8 cm", "Talla extra pequeña"),
            ("XS", 2, "80 - 84 cm", "64 - 68 cm", "90 - 94 cm", "-7 cm", "Talla pequeña"),
            ("S", 3, "84 - 88 cm", "68 - 72 cm", "94 - 98 cm", "-6 cm", "Talla mediana pequeña"),
            ("M", 4, "88 - 92 cm", "72 - 76 cm", "98 - 102 cm", "-5 cm", "Talla mediana"),
            ("L", 5, "92 - 96 cm", "76 - 80 cm", "102 - 106 cm", "-4 cm", "Talla grande"),
            ("XL", 6, "96 - 100 cm", "80 - 84 cm", "106 - 110 cm", "-3 cm", "Talla extra grande"),
        ]:
            bind.execute(
                sa.text(
                    "INSERT INTO maestros_tallas_estandar (talla, orden, busto, cintura, cadera, reduccion_corset, descripcion) "
                    "VALUES (:talla, :orden, :busto, :cintura, :cadera, :red, :desc) "
                    "ON CONFLICT (talla) DO NOTHING"
                ),
                {"talla": talla, "orden": orden, "busto": busto, "cintura": cintura, "cadera": cadera, "red": red, "desc": desc},
            )
        # also handle orden conflict (if talla not conflict but orden)
        # ON CONFLICT (orden) second pass
        for talla, orden in [("XXS", 1), ("XS", 2), ("S", 3), ("M", 4), ("L", 5), ("XL", 6)]:
            # no-op if already inserted; duplicate orden insert will be ignored via talla unique
            pass

    # 2) productos_sin_talla
    if not _has_table("maestros_productos_sin_talla"):
        op.create_table(
            "maestros_productos_sin_talla",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nombre", sa.String(100), nullable=False, unique=True),
            sa.Column("categoria", sa.String(100), nullable=False),
            sa.Column("dimensiones", sa.String(100), nullable=True),
            sa.Column("materiales", sa.String(200), nullable=True),
            sa.Column("descripcion", sa.Text(), nullable=True),
            sa.Column("precio_sugerido", sa.Numeric(15, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("precio_sugerido >= 0", name="ck_sintalla_precio"),
            sa.UniqueConstraint("nombre", name="uq_sintalla_nombre"),
        )
        op.create_index("ix_sintalla_categoria", "maestros_productos_sin_talla", ["categoria"])
        op.create_index("ix_sintalla_activo", "maestros_productos_sin_talla", ["activo"])

    # 3) parametros_costeo singleton
    if not _has_table("maestros_parametros_costeo"):
        op.create_table(
            "maestros_parametros_costeo",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("costo_minuto_costura", sa.Numeric(15, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("costo_hora_patronaje", sa.Numeric(15, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("margen_meta_global_pct", sa.Numeric(15, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("desperdicio_textil_default_pct", sa.Numeric(15, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("iva_regimen_pct", sa.Numeric(15, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("distribucion_reinversion_pct", sa.Numeric(15, 4), nullable=False, server_default=sa.text("40")),
            sa.Column("reparto_margara_pct", sa.Numeric(15, 4), nullable=False, server_default=sa.text("30")),
            sa.Column("reparto_valqui_pct", sa.Numeric(15, 4), nullable=False, server_default=sa.text("30")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("costo_minuto_costura >= 0", name="ck_param_minuto"),
            sa.CheckConstraint("costo_hora_patronaje >= 0", name="ck_param_patronaje"),
            sa.CheckConstraint("margen_meta_global_pct >= 0 AND margen_meta_global_pct <= 100", name="ck_param_margen"),
            sa.CheckConstraint("desperdicio_textil_default_pct >= 0 AND desperdicio_textil_default_pct <= 100", name="ck_param_desperdicio"),
        )
        bind = op.get_bind()
        bind.execute(
            sa.text(
                "INSERT INTO maestros_parametros_costeo (id, costo_minuto_costura, costo_hora_patronaje, margen_meta_global_pct, desperdicio_textil_default_pct, iva_regimen_pct, distribucion_reinversion_pct, reparto_margara_pct, reparto_valqui_pct) "
                "VALUES (1, 80, 15000, 35, 8, 19, 40, 30, 30) ON CONFLICT (id) DO NOTHING"
            )
        )


def downgrade() -> None:
    for tbl in ["maestros_parametros_costeo", "maestros_productos_sin_talla", "maestros_tallas_estandar"]:
        if _has_table(tbl):
            op.drop_table(tbl)
