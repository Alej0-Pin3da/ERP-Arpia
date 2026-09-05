"""Indexes on audit/omisiones filter columns (P2 auditoría funcional).

- precio_versions(producto_id), costo_versions(producto_id): filtered by the
  audit-fiscal GETs; FK columns with no index also slow parent deletes.
- Migracion_Omisiones(resuelta), Migracion_Omisiones(nivel): the
  /omisiones filters (resuelta/nivel/fase). periodo on cierres_mensuales
  is UNIQUE, so already indexed.
- Idempotent CREATE INDEX IF NOT EXISTS (never fails, never poisons the
  transaction). Downgrade drops them the same way.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027_audit_omisiones_indexes"
down_revision: str | None = "0026_pedidos_cliente_fk"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

INDEXES = [
    ("ix_precio_versions_producto_id", "precio_versions", "producto_id"),
    ("ix_costo_versions_producto_id", "costo_versions", "producto_id"),
    ("ix_migracion_omisiones_resuelta", "Migracion_Omisiones", "resuelta"),
    ("ix_migracion_omisiones_nivel", "Migracion_Omisiones", "nivel"),
]


def upgrade() -> None:
    bind = op.get_bind()
    for name, table, column in INDEXES:
        try:
            bind.execute(
                sa.text(f'CREATE INDEX IF NOT EXISTS "{name}" ON "{table}" ("{column}")')
            )
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    for name, table, _column in INDEXES:
        try:
            bind.execute(sa.text(f'DROP INDEX IF EXISTS "{name}"'))
        except Exception:
            pass
