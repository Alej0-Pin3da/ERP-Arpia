"""Persisted quick quotes (0043).

- `Cotizaciones` header table: pricing-inputs snapshot + server-computed
  results (costo_total, precio_sugerido, ganancia_neta). `codigo` is derived
  (COT-0001), never stored. `estado` CHECK borrador|enviada|aprobada|
  descartada.

Idempotent guard: skip when the table already exists. Downgrade drops it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0043_cotizaciones"
down_revision: str | None = "0042_venta_observaciones"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "Cotizaciones"


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return sa.inspect(bind).has_table(table)
    except Exception:
        return False


def upgrade() -> None:
    if _has_table(TABLE):
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "cliente_id",
            sa.Integer(),
            sa.ForeignKey("Clientes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "producto_id",
            sa.Integer(),
            sa.ForeignKey("Productos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("nombre_prenda", sa.String(255), nullable=False),
        sa.Column("metros_tela", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("precio_metro_tela", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("metros_forro", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("precio_metro_forro", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("costo_avios", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("costo_empaque", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("tiempo_confeccion_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tarifa_hora", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("costo_cif", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("margen_pct", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("costo_total", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("precio_sugerido", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("ganancia_neta", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="borrador"),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "estado IN ('borrador', 'enviada', 'aprobada', 'descartada')",
            name="ck_cotizaciones_estado",
        ),
    )
    op.create_index("ix_cotizaciones_cliente", TABLE, ["cliente_id"])
    op.create_index("ix_cotizaciones_producto", TABLE, ["producto_id"])
    op.create_index("ix_cotizaciones_estado", TABLE, ["estado"])
    op.create_index("ix_cotizaciones_fecha", TABLE, ["fecha"])


def downgrade() -> None:
    bind = op.get_bind()
    # DROP ... IF EXISTS never errors, so it cannot poison the transaction.
    # NOTE: identifiers are quoted - unquoted names fold to lowercase
    # and IF EXISTS would silently miss them.
    bind.execute(sa.text(f'DROP TABLE IF EXISTS "{TABLE}"'))
