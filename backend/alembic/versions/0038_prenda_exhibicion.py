"""Exhibition state for finished garments (0038).

- `prendas_confeccionadas.estado` gains 'exhibicion' (showroom/photos, NOT
  sellable): check `ck_prendas_confeccionadas_estado` rebuilt with the five
  values. Disponibles-para-venta logic (estado == 'disponible') is untouched.
- Idempotent guards: drop/create the named check only when needed; never
  CAST(:table AS regclass). Downgrade restores the four-value check.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0038_prenda_exhibicion"
down_revision: str | None = "0037_maestros_cat_producto"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "prendas_confeccionadas"
CHECK = "ck_prendas_confeccionadas_estado"
OLD_VALUES = "('disponible', 'reservada', 'vendida', 'defectuosa')"
NEW_VALUES = "('disponible', 'reservada', 'vendida', 'defectuosa', 'exhibicion')"


def _check_def() -> str | None:
    bind = op.get_bind()
    try:
        return bind.execute(
            sa.text(
                "SELECT pg_get_constraintdef(c.oid) FROM pg_constraint c "
                "JOIN pg_class cl ON cl.oid = c.conrelid "
                "WHERE c.conname = :name AND cl.relname = :table AND c.contype = 'c'"
            ),
            {"name": CHECK, "table": TABLE},
        ).scalar()
    except Exception:
        return None


def upgrade() -> None:
    definition = _check_def()
    if definition is None or "exhibicion" not in definition:
        bind = op.get_bind()
        bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP CONSTRAINT IF EXISTS "{CHECK}"'))
        bind.execute(
            sa.text(
                f'ALTER TABLE "{TABLE}" ADD CONSTRAINT "{CHECK}" '
                f"CHECK (estado IN {NEW_VALUES})"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text(f'ALTER TABLE "{TABLE}" DROP CONSTRAINT IF EXISTS "{CHECK}"'))
    bind.execute(
        sa.text(
            f'ALTER TABLE "{TABLE}" ADD CONSTRAINT "{CHECK}" '
            f"CHECK (estado IN {OLD_VALUES})"
        )
    )
