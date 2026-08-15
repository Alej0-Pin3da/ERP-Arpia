from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CompraInsumoCreate(BaseModel):
    insumo_id: int
    cantidad_comprada: Decimal = Field(gt=0)
    precio_unitario_compra: Decimal = Field(ge=0)


class CompraInsumoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    insumo_id: int
    fecha_compra: datetime
    cantidad_comprada: Decimal
    precio_unitario_compra: Decimal
