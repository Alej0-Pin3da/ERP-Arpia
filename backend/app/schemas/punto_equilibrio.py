from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class PuntoEquilibrioRead(BaseModel):
    """Termómetro Operativo del Mes (read-only snapshot, all Decimal).

    estado drives the frontend render:
    - sin_datos: no confirmed sales this month (no bar, neutral note).
    - sin_configurar: costos_fijos_mensuales is 0/unset (hint to Maestros).
    - alerta: month margin <= 0 (fixed red alert, no bar, no meta).
    - en_camino: below goal (amber bar + faltante).
    - superada: goal met (emerald bar + utilidad_extra).
    """

    periodo: str
    estado: Literal["sin_datos", "sin_configurar", "alerta", "en_camino", "superada"]
    ventas_netas: Decimal
    costos_netos: Decimal
    margen_pct: Decimal
    costos_fijos: Decimal
    meta_ventas: Decimal | None
    avance_pct: Decimal | None
    faltante: Decimal | None
    utilidad_extra: Decimal | None
    n_ventas: int
    n_devoluciones: int
