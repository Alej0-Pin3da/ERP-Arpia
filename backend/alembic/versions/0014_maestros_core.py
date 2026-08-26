"""maestros core: 3 CREATE + 2 ALTER stubs with _has_* guards <400 lines

Revision ID: 0014_maestros_core
Revises: 0013_create_anticipos
Create Date: 2026-08-25

- CREATE maestros_proveedores, maestros_categorias_coleccion, maestros_ubicaciones_taller
- ALTER maestros_canales_venta + maestros_metodos_pago (extend 0010 stubs, nullable, _has_column)
- ON CONFLICT idempotent where needed, CHECK enums, NUMERIC(15,4), TIMESTAMPTZ
- downgrade drops cols only for stubs, DROP new tables
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_maestros_core"
down_revision: str | None = "0013_create_anticipos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return table in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        return column in [c["name"] for c in insp.get_columns(table)]
    except Exception:
        return False


def _has_index(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        return name in [i["name"] for i in sa.inspect(bind).get_indexes(table)]
    except Exception:
        return False


def _has_constraint(table: str, name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        for c in insp.get_check_constraints(table):
            if c["name"] == name:
                return True
    except Exception:
        pass
    try:
        res = bind.execute(
            sa.text("SELECT 1 FROM pg_constraint WHERE conname=:name AND conrelid=CAST(:table AS regclass)"),
            {"name": name, "table": table},
        ).scalar()
        return res is not None
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # 1) maestros_proveedores
    if not _has_table("maestros_proveedores"):
        op.create_table(
            "maestros_proveedores",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nombre", sa.String(100), nullable=False, unique=True),
            sa.Column("categoria", sa.String(100), nullable=False),
            sa.Column("ciudad", sa.String(80), nullable=True),
            sa.Column("calificacion", sa.Numeric(3, 1), nullable=True),
            sa.Column("tiempo_entrega_dias", sa.Integer(), nullable=True),
            sa.Column("email", sa.String(255), nullable=True),
            sa.Column("telefono", sa.String(50), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("notas", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("calificacion IS NULL OR (calificacion >= 0 AND calificacion <= 5)", name="ck_proveedores_calificacion"),
            sa.CheckConstraint("tiempo_entrega_dias IS NULL OR tiempo_entrega_dias >= 0", name="ck_proveedores_tiempo_entrega"),
            sa.UniqueConstraint("nombre", name="uq_proveedores_nombre"),
        )
        op.create_index("ix_proveedores_categoria", "maestros_proveedores", ["categoria"])
        op.create_index("ix_proveedores_ciudad", "maestros_proveedores", ["ciudad"])
        op.create_index("ix_proveedores_activo", "maestros_proveedores", ["activo"])

    # 2) maestros_categorias_coleccion
    if not _has_table("maestros_categorias_coleccion"):
        op.create_table(
            "maestros_categorias_coleccion",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nombre", sa.String(100), nullable=False, unique=True),
            sa.Column("tipo_talla", sa.String(30), nullable=False),
            sa.Column("descripcion", sa.Text(), nullable=True),
            sa.Column("margen_meta_pct", sa.Numeric(15, 4), nullable=True),
            sa.Column("total_modelos", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("tipo_talla IN ('CON_TALLAS_ESTANDAR','SIN_TALLA_MERCH','TALLA_UNICA')", name="ck_categorias_tipo_talla"),
            sa.CheckConstraint("margen_meta_pct IS NULL OR (margen_meta_pct >= 0 AND margen_meta_pct <= 100)", name="ck_categorias_margen"),
            sa.CheckConstraint("total_modelos >= 0", name="ck_categorias_total_modelos"),
            sa.UniqueConstraint("nombre", name="uq_categorias_nombre"),
        )
        op.create_index("ix_categorias_tipo_talla", "maestros_categorias_coleccion", ["tipo_talla"])
        op.create_index("ix_categorias_activo", "maestros_categorias_coleccion", ["activo"])

    # 3) maestros_ubicaciones_taller
    if not _has_table("maestros_ubicaciones_taller"):
        op.create_table(
            "maestros_ubicaciones_taller",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("codigo", sa.String(20), nullable=False, unique=True),
            sa.Column("nombre", sa.String(100), nullable=False, unique=True),
            sa.Column("tipo", sa.String(30), nullable=False),
            sa.Column("capacidad", sa.String(100), nullable=True),
            sa.Column("observaciones", sa.Text(), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("codigo LIKE 'UB-%'", name="ck_ubicaciones_codigo_ub"),
            sa.CheckConstraint("tipo IN ('ROLLOS_TELAS','GAVETAS_HERRAJES','PERCHERO_SHOWROOM','ACCESORIOS_BODEGA')", name="ck_ubicaciones_tipo"),
            sa.UniqueConstraint("codigo", name="uq_ubicaciones_codigo"),
            sa.UniqueConstraint("nombre", name="uq_ubicaciones_nombre"),
        )
        op.create_index("ix_ubicaciones_tipo", "maestros_ubicaciones_taller", ["tipo"])
        op.create_index("ix_ubicaciones_activo", "maestros_ubicaciones_taller", ["activo"])
        op.create_index("ix_ubicaciones_codigo", "maestros_ubicaciones_taller", ["codigo"])

    # 4) ALTER maestros_canales_venta — extend stub (0010)
    if _has_table("maestros_canales_venta"):
        if not _has_column("maestros_canales_venta", "tipo"):
            op.add_column("maestros_canales_venta", sa.Column("tipo", sa.String(20), nullable=True))
        if not _has_column("maestros_canales_venta", "comision_pct"):
            op.add_column("maestros_canales_venta", sa.Column("comision_pct", sa.Numeric(15, 4), nullable=True))
        if not _has_column("maestros_canales_venta", "costo_fijo_mensual"):
            op.add_column("maestros_canales_venta", sa.Column("costo_fijo_mensual", sa.Numeric(15, 4), nullable=True))
        if not _has_column("maestros_canales_venta", "activo"):
            op.add_column("maestros_canales_venta", sa.Column("activo", sa.Boolean(), nullable=True, server_default=sa.text("true")))
        if not _has_column("maestros_canales_venta", "descripcion"):
            op.add_column("maestros_canales_venta", sa.Column("descripcion", sa.Text(), nullable=True))
        if not _has_column("maestros_canales_venta", "updated_at"):
            op.add_column("maestros_canales_venta", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True))
        # CHECKs idempotent
        if not _has_constraint("maestros_canales_venta", "ck_canales_tipo"):
            op.create_check_constraint("ck_canales_tipo", "maestros_canales_venta", "tipo IS NULL OR tipo IN ('FISICO','DIGITAL','EVENTO')")
        if not _has_constraint("maestros_canales_venta", "ck_canales_comision"):
            op.create_check_constraint("ck_canales_comision", "maestros_canales_venta", "comision_pct IS NULL OR (comision_pct >= 0 AND comision_pct <= 100)")
        if not _has_index("maestros_canales_venta", "ix_canales_tipo"):
            op.create_index("ix_canales_tipo", "maestros_canales_venta", ["tipo"])
        if not _has_index("maestros_canales_venta", "ix_canales_activo"):
            op.create_index("ix_canales_activo", "maestros_canales_venta", ["activo"])

    # 5) ALTER maestros_metodos_pago — extend stub (0010)
    if _has_table("maestros_metodos_pago"):
        if not _has_column("maestros_metodos_pago", "tipo"):
            op.add_column("maestros_metodos_pago", sa.Column("tipo", sa.String(30), nullable=True))
        if not _has_column("maestros_metodos_pago", "comision_pct"):
            op.add_column("maestros_metodos_pago", sa.Column("comision_pct", sa.Numeric(15, 4), nullable=True))
        if not _has_column("maestros_metodos_pago", "tiempo_acreditacion"):
            op.add_column("maestros_metodos_pago", sa.Column("tiempo_acreditacion", sa.String(50), nullable=True))
        if not _has_column("maestros_metodos_pago", "activo"):
            op.add_column("maestros_metodos_pago", sa.Column("activo", sa.Boolean(), nullable=True, server_default=sa.text("true")))
        if not _has_column("maestros_metodos_pago", "datos_cuenta"):
            op.add_column("maestros_metodos_pago", sa.Column("datos_cuenta", sa.Text(), nullable=True))
        if not _has_column("maestros_metodos_pago", "descripcion"):
            op.add_column("maestros_metodos_pago", sa.Column("descripcion", sa.Text(), nullable=True))
        if not _has_column("maestros_metodos_pago", "updated_at"):
            op.add_column("maestros_metodos_pago", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True))
        if not _has_constraint("maestros_metodos_pago", "ck_metodos_tipo"):
            op.create_check_constraint("ck_metodos_tipo", "maestros_metodos_pago", "tipo IS NULL OR tipo IN ('TRANSFERENCIA','BILLETERA_DIGITAL','EFECTIVO','PASARELA_DATAFONO')")
        if not _has_constraint("maestros_metodos_pago", "ck_metodos_comision"):
            op.create_check_constraint("ck_metodos_comision", "maestros_metodos_pago", "comision_pct IS NULL OR (comision_pct >= 0 AND comision_pct <= 100)")
        if not _has_index("maestros_metodos_pago", "ix_metodos_tipo"):
            op.create_index("ix_metodos_tipo", "maestros_metodos_pago", ["tipo"])
        if not _has_index("maestros_metodos_pago", "ix_metodos_activo"):
            op.create_index("ix_metodos_activo", "maestros_metodos_pago", ["activo"])


def downgrade() -> None:
    bind = op.get_bind()

    # Drop new tables
    for tbl in ["maestros_ubicaciones_taller", "maestros_categorias_coleccion", "maestros_proveedores"]:
        if _has_table(tbl):
            op.drop_table(tbl)

    # Revert ALTERs — drop added columns from stubs, keep tables
    if _has_table("maestros_canales_venta"):
        for ck in ["ck_canales_comision", "ck_canales_tipo"]:
            if _has_constraint("maestros_canales_venta", ck):
                try:
                    op.drop_constraint(ck, "maestros_canales_venta", type_="check")
                except Exception:
                    try:
                        bind.execute(sa.text(f'ALTER TABLE maestros_canales_venta DROP CONSTRAINT IF EXISTS {ck}'))
                    except Exception:
                        pass
        for idx in ["ix_canales_activo", "ix_canales_tipo"]:
            if _has_index("maestros_canales_venta", idx):
                try:
                    op.drop_index(idx, table_name="maestros_canales_venta")
                except Exception:
                    pass
        for col in ["updated_at", "descripcion", "activo", "costo_fijo_mensual", "comision_pct", "tipo"]:
            if _has_column("maestros_canales_venta", col):
                op.drop_column("maestros_canales_venta", col)

    if _has_table("maestros_metodos_pago"):
        for ck in ["ck_metodos_comision", "ck_metodos_tipo"]:
            if _has_constraint("maestros_metodos_pago", ck):
                try:
                    op.drop_constraint(ck, "maestros_metodos_pago", type_="check")
                except Exception:
                    try:
                        bind.execute(sa.text(f'ALTER TABLE maestros_metodos_pago DROP CONSTRAINT IF EXISTS {ck}'))
                    except Exception:
                        pass
        for idx in ["ix_metodos_activo", "ix_metodos_tipo"]:
            if _has_index("maestros_metodos_pago", idx):
                try:
                    op.drop_index(idx, table_name="maestros_metodos_pago")
                except Exception:
                    pass
        for col in ["updated_at", "descripcion", "datos_cuenta", "activo", "tiempo_acreditacion", "comision_pct", "tipo"]:
            if _has_column("maestros_metodos_pago", col):
                op.drop_column("maestros_metodos_pago", col)
