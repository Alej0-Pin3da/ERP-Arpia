"""Pydantic schemas for the automatic profit split (V6 M2).

Percentages and balances are Decimal. Rules are managed by admin/operador;
balances are read-only computed state (the split itself happens inside the
sale transaction, never through these schemas).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReglaCreate(BaseModel):
    cuenta_destino: str = Field(min_length=1, max_length=100)
    porcentaje: Decimal = Field(ge=0)


class ReglaUpdate(BaseModel):
    cuenta_destino: str | None = Field(default=None, min_length=1, max_length=100)
    porcentaje: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = None


class ReglaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cuenta_destino: str
    porcentaje: Decimal
    activo: bool


class SaldoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cuenta: str
    saldo: Decimal
    actualizado_en: datetime


class RepartoVentaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    venta_id: int
    cuenta: str
    monto: Decimal
