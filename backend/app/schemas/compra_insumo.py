from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CompraInsumoCreate(BaseModel):
    insumo_id: int
    proveedor_id: int | None = None
    cantidad_comprada: Decimal = Field(gt=0)
    precio_unitario_compra: Decimal = Field(ge=0)


class CompraInsumoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    insumo_id: int
    proveedor_id: int | None
    fecha_compra: datetime
    cantidad_comprada: Decimal
    precio_unitario_compra: Decimal
    # Not an ORM attribute: populated by the route from the eager-loaded
    # proveedor relationship (None when proveedor_id is NULL).
    nombre_proveedor: str | None = None
