"""Tiempos por fase + tarifa global de energia.

- `maestros_parametros_costeo.costo_minuto_energia` NUMERIC(15,4) NOT NULL
  DEFAULT 0 + CHECK >= 0 (`ck_param_energia`): segunda tarifa global junto a
  `costo_minuto_costura` (costo_hora_patronaje intacto).
- CREATE `produccion_tiempos_fase`: minutos reales por fase trabajada con
  operaria. `pedido_id` FK -> pedidos_produccion CASCADE, `fase` CHECK
  (corte | costura | acabados | calidad — `listo` cierra el lote, no se
  registra), `minutos_reales` NUMERIC(10,2) CHECK > 0, `fecha` DATE DEFAULT
  today, UNIQUE (pedido_id, fase): un renglon por fase, el segundo POST es
  409 y las correcciones van por PATCH.

Idempotent guards (style 0014/0022/0024/0030): exact table/column/check
probing, never CAST(:table AS regclass). Downgrade drops the table, then
the CHECK and the column.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0031_tiempos_fase_energia"
down_revision: str | None = "0030_produccion_fase_stock"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

CK_PARAM_ENERGIA = "ck_param_energia"
PARAM_ENERGIA_CHECK = "costo_minuto_energia >= 0"
CK_TIEMPOS_MINUTOS = "ck_tiempos_minutos_pos"
CK_TIEMPOS_FASE = "ck_tiempos_fase"
TIEMPOS_FASE_CHECK = "fase IN ('corte', 'costura', 'acabados', 'calidad')"
UQ_TIEMPOS_PEDIDO_FASE = "uq_tiempos_pedido_fase"
IX_TIEMPOS_PEDIDO = "ix_tiempos_pedido"


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


def _has_index(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        return name in [i["name"] for i in sa.inspect(bind).get_indexes(table)]
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table("maestros_parametros_costeo"):
        if not _has_column("maestros_parametros_costeo", "costo_minuto_energia"):
            op.add_column(
                "maestros_parametros_costeo",
                sa.Column(
                    "costo_minuto_energia",
                    sa.Numeric(15, 4),
                    nullable=False,
                    server_default="0",
                ),
            )
        if not _has_check("maestros_parametros_costeo", CK_PARAM_ENERGIA):
            op.create_check_constraint(
                CK_PARAM_ENERGIA, "maestros_parametros_costeo", PARAM_ENERGIA_CHECK
            )
    if not _has_table("produccion_tiempos_fase"):
        op.create_table(
            "produccion_tiempos_fase",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "pedido_id",
                sa.Integer(),
                sa.ForeignKey("pedidos_produccion.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("fase", sa.String(20), nullable=False),
            sa.Column("operaria", sa.String(150), nullable=False),
            sa.Column("minutos_reales", sa.Numeric(10, 2), nullable=False),
            sa.Column(
                "fecha",
                sa.Date(),
                nullable=False,
                server_default=sa.text("CURRENT_DATE"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.CheckConstraint("minutos_reales > 0", name=CK_TIEMPOS_MINUTOS),
            sa.CheckConstraint(TIEMPOS_FASE_CHECK, name=CK_TIEMPOS_FASE),
            sa.UniqueConstraint("pedido_id", "fase", name=UQ_TIEMPOS_PEDIDO_FASE),
        )
    if _has_table("produccion_tiempos_fase") and not _has_index(
        "produccion_tiempos_fase", IX_TIEMPOS_PEDIDO
    ):
        op.create_index(IX_TIEMPOS_PEDIDO, "produccion_tiempos_fase", ["pedido_id"])
    # Normalize legacy/out-of-range values (never delete rows, 0024 style).
    if _has_table("produccion_tiempos_fase"):
        bind.execute(
            sa.text(
                "DELETE FROM produccion_tiempos_fase "
                "WHERE fase NOT IN ('corte', 'costura', 'acabados', 'calidad') "
                "OR minutos_reales <= 0"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text('DROP TABLE IF EXISTS "produccion_tiempos_fase"'))
    bind.execute(
        sa.text(
            "ALTER TABLE maestros_parametros_costeo DROP CONSTRAINT IF EXISTS "
            f'"{CK_PARAM_ENERGIA}"'
        )
    )
    bind.execute(
        sa.text(
            'ALTER TABLE maestros_parametros_costeo DROP COLUMN IF EXISTS "costo_minuto_energia"'
        )
    )
