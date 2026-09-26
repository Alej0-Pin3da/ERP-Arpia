"""Cotizaciones: desperdicio e hilos (0045).

- desperdicio_pct: merma de corte sobre telas (%, como el BOM). El servidor
  lo aplica en _calcular para paridad con el frontend.
- costo_hilo_m / metros_hilo: snapshot informativo de la estimación de hilos
  (no entran al costo; el costo entra vía costo_avios cuando se aplica).

Default 0: las cotizaciones existentes calculan igual que antes.
Downgrade: quita las 3 columnas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0045_cotizaciones_hilos"
down_revision: str | None = "0044_anticipos_multi_descuento"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    for col in ("desperdicio_pct", "costo_hilo_m", "metros_hilo"):
        try:
            op.add_column(
                "Cotizaciones",
                sa.Column(col, sa.Numeric(15, 4), nullable=False, server_default="0"),
            )
        except Exception:
            pass


def downgrade() -> None:
    for col in ("metros_hilo", "costo_hilo_m", "desperdicio_pct"):
        try:
            op.drop_column("Cotizaciones", col)
        except Exception:
            pass
