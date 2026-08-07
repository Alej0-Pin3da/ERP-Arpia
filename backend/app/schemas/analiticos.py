"""Pydantic schemas for the read-only analiticos API surface.

All three payloads are read-only aggregations. Money/quantities stay
NUMERIC(15,4) (Decimals); the margin rows come ONLY from the
``Detalle_Ventas.costo_unitario_aplicado`` snapshot — never the current WAC.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class VentasMensualesRead(BaseModel):
    mes: date
    total: Decimal
    cantidad: int


class InsumoBajoStockRead(BaseModel):
    insumo_id: int
    nombre: str
    unidad_medida: str
    stock_actual: Decimal
    stock_minimo: Decimal


class MargenProductoRead(BaseModel):
    producto_id: int
    variante_id: int | None
    margen_total: Decimal
    margen_promedio: Decimal
