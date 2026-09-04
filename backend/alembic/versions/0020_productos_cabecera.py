"""productos cabecera: categoria, linea, descripcion, tiempo, costos split, markup, recomendaciones, codigo, fases"""
from collections.abc import Sequence
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0020_productos_cabecera"
down_revision: str | None = "0019_audit_fiscal_versioning"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        cols = [c["name"] for c in insp.get_columns(table)]
        return column in cols
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
    # NOTE: never use CAST(:table AS regclass) here — regclass folds
    # unquoted names to lowercase, so it raises UndefinedTable for
    # case-sensitive tables ("Productos", "Ventas", ...) and the failed
    # statement poisons the whole migration transaction. The JOIN on
    # pg_class.relname matches exactly and never errors.
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint c JOIN pg_class cl "
                "ON cl.oid = c.conrelid "
                "WHERE c.conname = :name AND cl.relname = :table"
            ),
            {"name": name, "table": table},
        ).scalar()
        return res is not None
    except Exception:
        return False


def _has_index(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        return name in [i["name"] for i in sa.inspect(bind).get_indexes(table)]
    except Exception:
        return False


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
        ("fases", JSONB(), {"nullable": True}),
    ]
    for col_name, col_type, kwargs in cols_to_add:
        if not _has_column(tbl, col_name):
            op.add_column(tbl, sa.Column(col_name, col_type, **kwargs))

    # Checks (nullable, only when not null). Guarded, never try/except around
    # DDL: a failed statement inside Postgres transactional DDL poisons the
    # whole migration transaction (0020 broke fresh DBs this way).
    checks = [
        ("ck_productos_tiempo_confeccion_min", "tiempo_confeccion_min IS NULL OR tiempo_confeccion_min >= 0"),
        ("ck_productos_costo_insumos", "costo_insumos IS NULL OR costo_insumos >= 0"),
        ("ck_productos_mano_obra", "mano_obra IS NULL OR mano_obra >= 0"),
        ("ck_productos_cif_energia", "cif_energia IS NULL OR cif_energia >= 0"),
    ]
    for name, sql in checks:
        if not _has_constraint(tbl, name):
            op.create_check_constraint(name, tbl, sql)
    # Drop old 0-100 markup constraint if it exists from a previous 0020
    # attempt, then create with -1000..1000. DROP ... IF EXISTS never errors,
    # so it cannot poison the transaction.
    bind = op.get_bind()
    bind.execute(sa.text('ALTER TABLE "Productos" DROP CONSTRAINT IF EXISTS ck_productos_markup_pct'))
    op.create_check_constraint("ck_productos_markup_pct", tbl, "markup_pct IS NULL OR (markup_pct >= -1000 AND markup_pct <= 1000)")

    # Indexes for filtering
    for idx, cols in [
        ("ix_productos_codigo", ["codigo"]),
        ("ix_productos_categoria", ["categoria"]),
        ("ix_productos_linea", ["linea"]),
    ]:
        if not _has_index(tbl, idx):
            op.create_index(idx, tbl, cols, unique=(idx == "ix_productos_codigo"))


def downgrade() -> None:
    tbl = "Productos"
    bind = op.get_bind()
    for c in ["ck_productos_tiempo_confeccion_min", "ck_productos_costo_insumos", "ck_productos_mano_obra", "ck_productos_cif_energia", "ck_productos_markup_pct"]:
        bind.execute(sa.text(f'ALTER TABLE "{tbl}" DROP CONSTRAINT IF EXISTS {c}'))
    for idx in ["ix_productos_codigo", "ix_productos_categoria", "ix_productos_linea"]:
        if _has_index(tbl, idx):
            op.drop_index(idx, table_name=tbl)
    for col in ["fases", "recomendaciones_taller", "markup_pct", "cif_energia", "mano_obra", "costo_insumos", "tiempo_confeccion_min", "descripcion", "linea", "categoria", "codigo"]:
        if _has_column(tbl, col):
            op.drop_column(tbl, col)
