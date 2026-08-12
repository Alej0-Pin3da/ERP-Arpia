from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DetalleVentaCreate(BaseModel):
    producto_id: int
    variante_id: int | None = None
    cantidad: Decimal = Field(gt=0)
    precio_unitario: Decimal = Field(ge=0)


class VentaCreate(BaseModel):
    cliente_id: int | None = None
    canal_venta: Literal["web", "whatsapp", "instagram", "feria"]
    descuento_porcentaje: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    es_regalo: bool = False
    detalles: list[DetalleVentaCreate] = Field(min_length=1)


class VentaUpdate(BaseModel):
    es_regalo: bool


class DetalleVentaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    variante_id: int | None
    cantidad: Decimal
    precio_unitario_aplicado: Decimal
    costo_unitario_aplicado: Decimal


class VentaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    cliente_id: int | None
    canal_venta: str
    descuento_porcentaje: Decimal
    estado: str
    total_venta: Decimal
    es_regalo: bool
    detalles: list[DetalleVentaRead]