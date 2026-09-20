"""Per-phase STANDARD times on Productos (BOM/Ficha estimates, no pedido needed).

- `Productos.tiempo_corte_min / tiempo_costura_min / tiempo_acabados_min /
  tiempo_calidad_min` INTEGER NULL + CHECK >= 0 each
  (`ck_productos_tiempo_{corte,costura,acabados,calidad}_min`): estimated
  labor/CIF minutes per phase shown on BOM/Ficha without needing a pedido.
  NULL = no estimate yet (backward compat, no backfill).
- Taller/pedidos untouched: REAL times stay on TiempoFase
  (`produccion_tiempos_fase`); `completar_lote` NEVER overwrites these
  Producto estimates. Labor is NOT modeled as BomInsumo lines.

Idempotent guards (style 0031/0034/0035): exact table/column/check probing,
never CAST(:table AS regclass). Downgrade drops checks then columns.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0036_producto_tiempos_fase_std"
down_revision: str | None = "0035_bom_insumo_detalle"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "Productos"
COLUMNS = (
    "tiempo_corte_min",
    "tiempo_costura_min",
    "tiempo_acabados_min",
    "tiempo_calidad_min",
)
CHECKS = {
    "tiempo_corte_min": "ck_productos_tiempo_corte_min",
    "tiempo_costura_min": "ck_productos_tiempo_costura_min",
    "tiempo_acabados_min": "ck_productos_tiempo_acabados_min",
    "tiempo_calidad_min": "ck_productos_tiempo_calidad_min",
}


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return table in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    try:
        return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]
    except Exception:
        return False


def _has_check(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint c JOIN pg_class cl "
                "ON cl.oid = c.conrelid "
                "WHERE c.conname = :name AND cl.relname = :table "
                "AND c.contype = 'c'"
            ),
            {"name": name, "table": table},
        ).scalar()
        return res is not None
    except Exception:
        return False


def upgrade() -> None:
    if not _has_table(TABLE):
        return
    for column in COLUMNS:
        if not _has_column(TABLE, column):
            op.add_column(TABLE, sa.Column(column, sa.Integer(), nullable=True))
        check = CHECKS[column]
        if not _has_check(TABLE, check):
            op.create_check_constraint(check, TABLE, f"{column} >= 0")


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    for column in COLUMNS:
        bind.execute(
            sa.text(f'ALTER TABLE "{TABLE}" DROP CONSTRAINT IF EXISTS "{CHECKS[column]}"')
        )
    for column in COLUMNS:
        bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP COLUMN IF EXISTS "{column}"'))
