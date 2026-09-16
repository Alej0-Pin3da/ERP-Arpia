"""Devoluciones single-return hard backstop: UNIQUE(venta_id).

- `uq_devoluciones_venta_id` on "Devoluciones"("venta_id"): one return per
  sale at the DB level. The service already serializes concurrent returns
  (Venta FOR UPDATE + locked existing-Devolucion check -> 409); this
  constraint turns any residual race into an IntegrityError -> 409 instead
  of a double restock. Nothing is persisted on conflict (single commit).

Idempotent guards (style 0030/0031/0032): exact constraint probing via
pg_constraint, never CAST(:table AS regclass). Downgrade drops it.

RISK: if production already holds >1 Devolucion for the same venta_id
(app-level check predates this constraint), upgrade fails loudly with a
duplicate-key error and applies nothing — dedupe manually, then retry.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033_devolucion_venta_unique"
down_revision: str | None = "0032_coleccion_composicion"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_unique_constraint(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        return bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint "
                "WHERE conname = :name "
                "AND conrelid = (SELECT oid FROM pg_class WHERE relname = :table)"
            ),
            {"name": name, "table": table},
        ).scalar() is not None
    except Exception:
        return False


def upgrade() -> None:
    if not _has_unique_constraint("Devoluciones", "uq_devoluciones_venta_id"):
        op.create_unique_constraint(
            "uq_devoluciones_venta_id", "Devoluciones", ["venta_id"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP CONSTRAINT IF EXISTS never errors, so it cannot poison the txn.
    bind.execute(
        sa.text(
            'ALTER TABLE "Devoluciones" '
            'DROP CONSTRAINT IF EXISTS "uq_devoluciones_venta_id"'
        )
    )
