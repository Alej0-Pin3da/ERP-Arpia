"""Pydantic schemas for the cotizaciones API surface.

``CotizacionCreate`` carries only the pricing inputs (plus optional
cliente/producto links and notes); the server computes
``costo_total``/``precio_sugerido``/``ganancia_neta`` so every stored quote
uses the same math. ``CotizacionEstadoUpdate`` moves a quote along
borrador → enviada → aprobada/descartada.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoCotizacion = Literal["borrador", "enviada", "aprobada", "descartada"]


class InsumoCotizacion(BaseModel):
    """One dynamic BOM line: validated with Decimal parsing (no floats)."""

    nombre: str = Field(min_length=1, max_length=255)
    cantidad: Decimal = Field(gt=0)
    precio_unitario: Decimal = Field(ge=0)
    unidad_medida: str = Field(min_length=1, max_length=20)
    desperdicio_pct: Decimal = Field(default=Decimal("0"), ge=0)


class CotizacionCreate(BaseModel):
    cliente_id: int | None = None
    producto_id: int | None = None
    nombre_prenda: str = Field(min_length=1, max_length=255)
    insumos: list[InsumoCotizacion] = Field(default_factory=list)
    costo_avios: Decimal = Field(default=Decimal("0"), ge=0)
    costo_empaque: Decimal = Field(default=Decimal("0"), ge=0)
    tiempo_confeccion_min: int = Field(default=0, ge=0)
    tarifa_hora: Decimal = Field(default=Decimal("0"), ge=0)
    costo_cif: Decimal = Field(default=Decimal("0"), ge=0)
    margen_pct: Decimal = Field(default=Decimal("0"), ge=0)
    costo_hilo_m: Decimal = Field(default=Decimal("0"), ge=0)
    metros_hilo: Decimal = Field(default=Decimal("0"), ge=0)
    observaciones: str | None = None


class CotizacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str | None
    fecha: datetime
    cliente_id: int | None
    producto_id: int | None
    nombre_prenda: str
    insumos_detalle: list[InsumoCotizacion] = Field(default_factory=list)
    costo_avios: Decimal
    costo_empaque: Decimal
    tiempo_confeccion_min: int
    tarifa_hora: Decimal
    costo_cif: Decimal
    margen_pct: Decimal
    costo_hilo_m: Decimal
    metros_hilo: Decimal
    costo_total: Decimal
    precio_sugerido: Decimal
    ganancia_neta: Decimal
    estado: str
    observaciones: str | None
    creado_en: datetime


class CotizacionEstadoUpdate(BaseModel):
    """PATCH body: move the quote along its state machine."""

    estado: EstadoCotizacion
