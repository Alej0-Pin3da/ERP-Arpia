"""prendas_confeccionadas.variante_id nullable (P2-7).

The NOT NULL blocked generic/no-size garment stock (maestros_productos_sin_talla
had no bridge to prendas). The column becomes nullable; existing rows keep
their values (no backfill, nothing deleted — dev table was empty on
2026-09-03).

Downgrade: SET NOT NULL only when zero NULL rows exist; otherwise it raises
instead of touching data — revert the generic rows first, then downgrade.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025_prendas_variante_nullable"
down_revision: str | None = "0024_produccion_checks"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return table in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def _is_nullable(table: str, column: str) -> bool | None:
    bind = op.get_bind()
    try:
        for c in sa.inspect(bind).get_columns(table):
            if c["name"] == column:
                return bool(c.get("nullable", True))
        return None
    except Exception:
        return None


def upgrade() -> None:
    if not _has_table("prendas_confeccionadas"):
        return
    if _is_nullable("prendas_confeccionadas", "variante_id") is False:
        op.alter_column(
            "prendas_confeccionadas", "variante_id", existing_type=sa.Integer(), nullable=True
        )


def downgrade() -> None:
    if not _has_table("prendas_confeccionadas"):
        return
    if _is_nullable("prendas_confeccionadas", "variante_id") is not True:
        return
    bind = op.get_bind()
    nulls = bind.execute(
        sa.text("SELECT COUNT(*) FROM prendas_confeccionadas WHERE variante_id IS NULL")
    ).scalar()
    if nulls:
        raise RuntimeError(
            f"Cannot downgrade 0025: {nulls} prenda(s) with variante_id NULL exist. "
            "Revert them to a variante first — data is never deleted or rewritten."
        )
    op.alter_column(
        "prendas_confeccionadas", "variante_id", existing_type=sa.Integer(), nullable=False
    )
