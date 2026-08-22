"""Pydantic schemas for the read-only analiticos API surface.

All six payloads are read-only aggregations. Money/quantities stay
NUMERIC(15,4) (Decimals); the margin rows come ONLY from the
``Detalle_Ventas.costo_unitario_aplicado`` snapshot — never the current WAC.
Consumption metrics come from purchase records (``Compras_Insumos``), since
the DB has no production/consumption ledger.
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


class TopProductoRead(BaseModel):
    producto_id: int
    unidades: Decimal
    ingresos: Decimal


class TopInsumoRead(BaseModel):
    insumo_id: int
    nombre: str
    unidad_medida: str
    cantidad: Decimal


class FinanzasMensualesRead(BaseModel):
    mes: date
    ingresos: Decimal
    gastos: Decimal


class AnaliticosResumenRead(BaseModel):
    desde: date
    hasta: date
    ventas_total: Decimal
    cantidad_ventas: int
    unidades_vendidas: Decimal
    ticket_promedio: Decimal
    margen_total: Decimal
    gastos_total: Decimal
    resultado_neto: Decimal
    unidades_periodo_anterior: Decimal
    ticket_periodo_anterior: Decimal
    ventas_periodo_anterior: Decimal
    margen_periodo_anterior: Decimal
    gastos_periodo_anterior: Decimal
    resultado_periodo_anterior: Decimal
