"""CHECKs for production/garment enums (P2-4).

pedidos_produccion.estado/prioridad and prendas_confeccionadas.estado lived
only in backend/app/models/produccion.py (StrEnums) — invalid states could
enter via direct SQL. This adds three CHECKs mirroring the enums:

- pedidos_produccion.estado: pendiente | en_produccion | completado | cancelado
- pedidos_produccion.prioridad: baja | normal | alta | urgente
- prendas_confeccionadas.estado: disponible | reservada | vendida | defectuosa

Normalization (dev tables were empty on 2026-09-03, so these are no-ops
there, but they protect DBs with legacy data): any value outside the valid
set is mapped to the closest safe default — pedidos.estado -> 'pendiente',
pedidos.prioridad -> 'normal', prendas.estado -> 'disponible'. Rows are never
deleted.

Idempotent guards (_has_table/_has_column/_has_check with exact pg_class
match — never CAST(:table AS regclass)). Downgrade drops the three CHECKs.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024_produccion_checks"
down_revision: str | None = "0023_ventas_canal_metodo_fk"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

CK_PEDIDO_ESTADO = "ck_pedidos_produccion_estado"
CK_PEDIDO_PRIORIDAD = "ck_pedidos_produccion_prioridad"
CK_PRENDA_ESTADO = "ck_prendas_confeccionadas_estado"

PEDIDO_ESTADO_CHECK = (
    "estado IN ('pendiente', 'en_produccion', 'completado', 'cancelado')"
)
PEDIDO_PRIORIDAD_CHECK = "prioridad IN ('baja', 'normal', 'alta', 'urgente')"
PRENDA_ESTADO_CHECK = (
    "estado IN ('disponible', 'reservada', 'vendida', 'defectuosa')"
)


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
    bind = op.get_bind()
    if _has_table("pedidos_produccion"):
        if _has_column("pedidos_produccion", "estado"):
            # Invalid -> 'pendiente' (never delete rows).
            bind.execute(
                sa.text(
                    "UPDATE pedidos_produccion SET estado = 'pendiente' "
                    "WHERE estado NOT IN "
                    "('pendiente', 'en_produccion', 'completado', 'cancelado')"
                )
            )
            if not _has_check("pedidos_produccion", CK_PEDIDO_ESTADO):
                op.create_check_constraint(
                    CK_PEDIDO_ESTADO, "pedidos_produccion", PEDIDO_ESTADO_CHECK
                )
        if _has_column("pedidos_produccion", "prioridad"):
            # Invalid -> 'normal' (never delete rows).
            bind.execute(
                sa.text(
                    "UPDATE pedidos_produccion SET prioridad = 'normal' "
                    "WHERE prioridad NOT IN ('baja', 'normal', 'alta', 'urgente')"
                )
            )
            if not _has_check("pedidos_produccion", CK_PEDIDO_PRIORIDAD):
                op.create_check_constraint(
                    CK_PEDIDO_PRIORIDAD,
                    "pedidos_produccion",
                    PEDIDO_PRIORIDAD_CHECK,
                )
    if _has_table("prendas_confeccionadas"):
        if _has_column("prendas_confeccionadas", "estado"):
            # Invalid -> 'disponible' (never delete rows).
            bind.execute(
                sa.text(
                    "UPDATE prendas_confeccionadas SET estado = 'disponible' "
                    "WHERE estado NOT IN "
                    "('disponible', 'reservada', 'vendida', 'defectuosa')"
                )
            )
            if not _has_check("prendas_confeccionadas", CK_PRENDA_ESTADO):
                op.create_check_constraint(
                    CK_PRENDA_ESTADO, "prendas_confeccionadas", PRENDA_ESTADO_CHECK
                )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    bind.execute(
        sa.text(
            f"ALTER TABLE pedidos_produccion DROP CONSTRAINT IF EXISTS {CK_PEDIDO_ESTADO}"
        )
    )
    bind.execute(
        sa.text(
            f"ALTER TABLE pedidos_produccion DROP CONSTRAINT IF EXISTS {CK_PEDIDO_PRIORIDAD}"
        )
    )
    bind.execute(
        sa.text(
            f"ALTER TABLE prendas_confeccionadas DROP CONSTRAINT IF EXISTS {CK_PRENDA_ESTADO}"
        )
    )
