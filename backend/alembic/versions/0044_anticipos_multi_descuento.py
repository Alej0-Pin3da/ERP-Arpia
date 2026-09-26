"""Allow multiple anticipos per socia per liquidacion (0044).

crear_liquidacion links ALL PENDIENTE_DESCUENTO anticipos of each socia to the
new liquidacion in one transaction. The partial UNIQUE INDEX
ix_anticipos_socia_liquidacion ON anticipos (socia_id, liquidacion_id) WHERE
liquidacion_id IS NOT NULL (0013) only allows ONE anticipo per (socia,
liquidacion): a socia with 2 pending anticipos fails creation with 409
"Conflicto al crear la liquidación". Replace it with a non-unique index of
the same name so the link stays queryable but multi-discount works.
Double-discount of the SAME anticipo row is still guarded by the service
(estado + liquidacion_id check with FOR UPDATE -> 409).

Idempotent: skips when the index is already non-unique or missing.
Downgrade best-effort: restores the UNIQUE variant only when no duplicates
exist; otherwise keeps the non-unique index and reports.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0044_anticipos_multi_descuento"
down_revision: str | None = "0043_cotizaciones"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

INDEX = "ix_anticipos_socia_liquidacion"


def _indexes(table: str) -> dict:
    try:
        return {i["name"]: i for i in sa.inspect(op.get_bind()).get_indexes(table)}
    except Exception:
        return {}


def upgrade() -> None:
    idx = _indexes("anticipos").get(INDEX)
    if idx is None:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {INDEX} "
            "ON anticipos (socia_id, liquidacion_id) "
            "WHERE liquidacion_id IS NOT NULL"
        )
        return
    if not idx.get("unique", False):
        return
    op.execute(f"DROP INDEX IF EXISTS {INDEX}")
    op.execute(
        f"CREATE INDEX {INDEX} "
        "ON anticipos (socia_id, liquidacion_id) "
        "WHERE liquidacion_id IS NOT NULL"
    )


def downgrade() -> None:
    try:
        dup = op.get_bind().execute(
            sa.text(
                "SELECT 1 FROM anticipos WHERE liquidacion_id IS NOT NULL "
                "GROUP BY socia_id, liquidacion_id HAVING COUNT(*) > 1 LIMIT 1"
            )
        ).first()
    except Exception:
        dup = None
    if dup is not None:
        return
    op.execute(f"DROP INDEX IF EXISTS {INDEX}")
    op.execute(
        f"CREATE UNIQUE INDEX {INDEX} "
        "ON anticipos (socia_id, liquidacion_id) "
        "WHERE liquidacion_id IS NOT NULL"
    )
