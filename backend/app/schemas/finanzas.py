"""Pydantic schemas for the finanzas API surface.

Shape validation only: the sum-to-100 invariant and one-time-settlement rules
live in ``app.services.finanzas`` (the DB cannot express the multi-row
invariant as a CHECK constraint).
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MovimientoCreate(BaseModel):
    tipo: Literal["Gasto", "Inversion", "Retiro"]
    descripcion: str = Field(min_length=1, max_length=500)
    monto: Decimal = Field(gt=0)
    socio_id: int | None = None


class MovimientoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    tipo: str
    descripcion: str
    monto: Decimal
    socio_id: int | None
    estado: str
    liquidacion_id: str | None


class LiquidacionCreate(BaseModel):
    monto: Decimal = Field(gt=0)
    notas: str | None = None
    liquidacion_id: str | None = Field(default=None, max_length=10)


class SocioConfiguracionCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    porcentaje_participacion: Decimal = Field(gt=0)


class SocioConfiguracionUpdate(BaseModel):
    porcentaje_participacion: Decimal = Field(gt=0)


class SocioConfiguracionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    porcentaje_participacion: Decimal
