"""Master product categories + lines (Ficha dropdowns, owner-managed).

- `maestros_categorias_producto` (id, nombre, tipo CATEGORIA|LINEA, activo,
  timestamps): single master with tipo discriminator (no FK from Productos:
  categoria/linea stay free-text snapshots, so deleting a master row never
  breaks history).
- Seed: the 8 categories + 5 lines previously hardcoded in the Ficha
  (idempotent: inserts only missing (nombre, tipo)).

Idempotent guards (style 0031/0034/0035/0036): exact table probing, never
CAST(:table AS regclass). Downgrade drops the table.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0037_maestros_cat_producto"
down_revision: str | None = "0036_producto_tiempos_fase_std"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "maestros_categorias_producto"
SEED: tuple[tuple[str, str], ...] = (
    ("Corsetería", "CATEGORIA"),
    ("Blusas y Tops", "CATEGORIA"),
    ("Conjuntos y Sets", "CATEGORIA"),
    ("Vestidos", "CATEGORIA"),
    ("Pantalones", "CATEGORIA"),
    ("Accesorios", "CATEGORIA"),
    ("Alta Costura", "CATEGORIA"),
    ("General", "CATEGORIA"),
    ("Corsetería", "LINEA"),
    ("Prêt-à-Porter", "LINEA"),
    ("Lencería Fina", "LINEA"),
    ("Alta Costura", "LINEA"),
    ("General", "LINEA"),
)


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return table in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def upgrade() -> None:
    if not _has_table(TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nombre", sa.String(100), nullable=False),
            sa.Column("tipo", sa.String(20), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("tipo IN ('CATEGORIA','LINEA')", name="ck_catprod_tipo"),
            sa.UniqueConstraint("nombre", "tipo", name="uq_catprod_nombre_tipo"),
        )
    bind = op.get_bind()
    for nombre, tipo in SEED:
        bind.execute(
            sa.text(
                f'INSERT INTO "{TABLE}" (nombre, tipo) '
                "SELECT CAST(:nombre AS VARCHAR), CAST(:tipo AS VARCHAR) "
                f'WHERE NOT EXISTS (SELECT 1 FROM "{TABLE}" '
                "WHERE nombre = :nombre AND tipo = :tipo)"
            ),
            {"nombre": nombre, "tipo": tipo},
        )


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text(f'DROP TABLE IF EXISTS "{TABLE}"'))
