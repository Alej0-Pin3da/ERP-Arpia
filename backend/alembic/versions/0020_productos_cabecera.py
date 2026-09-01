"""productos cabecera: categoria, linea, descripcion, tiempo, costos split, markup, recomendaciones, codigo, fases"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0020_productos_cabecera"
down_revision: str | None = "0019_audit_fiscal_versioning"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    # Productos is "Productos" (capital P) per 0001
    tbl = "Productos"
    cols_to_add = [
        ("codigo", sa.String(50), {"unique": True, "nullable": True}),
        ("categoria", sa.String(100), {"nullable": True}),
        ("linea", sa.String(100), {"nullable": True}),
        ("descripcion", sa.Text(), {"nullable": True}),
        ("tiempo_confeccion_min", sa.Integer(), {"nullable": True}),
        ("costo_insumos", sa.Numeric(15, 4), {"nullable": True}),
        ("mano_obra", sa.Numeric(15, 4), {"nullable": True}),
        ("cif_energia", sa.Numeric(15, 4), {"nullable": True}),
        ("markup_pct", sa.Numeric(15, 4), {"nullable": True}),
        ("recomendaciones_taller", sa.Text(), {"nullable": True}),
        ("fases", sa.dialects.postgresql.JSONB(), {"nullable": True}),
    ]
    for col_name, col_type, kwargs in cols_to_add:
        if not _has_column(tbl, col_name):
            op.add_column(tbl, sa.Column(col_name, col_type, **kwargs))

    # Checks (nullable, only when not null)
    bind = op.get_bind()
    # Use try/except for idempotency if constraint already exists
    try:
        op.create_check_constraint("ck_productos_tiempo_confeccion_min", tbl, "tiempo_confeccion_min IS NULL OR tiempo_confeccion_min >= 0")
    except Exception:
        pass
    try:
        op.create_check_constraint("ck_productos_costo_insumos", tbl, "costo_insumos IS NULL OR costo_insumos >= 0")
    except Exception:
        pass
    try:
        op.create_check_constraint("ck_productos_mano_obra", tbl, "mano_obra IS NULL OR mano_obra >= 0")
    except Exception:
        pass
    try:
        op.create_check_constraint("ck_productos_cif_energia", tbl, "cif_energia IS NULL OR cif_energia >= 0")
    except Exception:
        pass
    # Drop old 0-100 constraint if it exists from a previous 0020 attempt, then create with -1000..1000
    try:
        op.drop_constraint("ck_productos_markup_pct", tbl, type_="check")
    except Exception:
        pass
    try:
        op.create_check_constraint("ck_productos_markup_pct", tbl, "markup_pct IS NULL OR (markup_pct >= -1000 AND markup_pct <= 1000)")
    except Exception:
        pass

    # Indexes for filtering
    for idx, cols in [
        ("ix_productos_codigo", ["codigo"]),
        ("ix_productos_categoria", ["categoria"]),
        ("ix_productos_linea", ["linea"]),
    ]:
        try:
            op.create_index(idx, tbl, cols, unique=(idx == "ix_productos_codigo"))
        except Exception:
            pass


def downgrade() -> None:
    tbl = "Productos"
    for c in ["ck_productos_tiempo_confeccion_min", "ck_productos_costo_insumos", "ck_productos_mano_obra", "ck_productos_cif_energia", "ck_productos_markup_pct"]:
        try:
            op.drop_constraint(c, tbl, type_="check")
        except Exception:
            pass
    for idx in ["ix_productos_codigo", "ix_productos_categoria", "ix_productos_linea"]:
        try:
            op.drop_index(idx, table_name=tbl)
        except Exception:
            pass
    for col in ["fases", "recomendaciones_taller", "markup_pct", "cif_energia", "mano_obra", "costo_insumos", "tiempo_confeccion_min", "descripcion", "linea", "categoria", "codigo"]:
        if _has_column(tbl, col):
            op.drop_column(tbl, col)
