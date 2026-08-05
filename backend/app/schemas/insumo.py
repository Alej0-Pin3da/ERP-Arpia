from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InsumoBase(BaseModel):
    categoria_id: int
    nombre: str = Field(min_length=1, max_length=255)
    unidad_medida: str = Field(min_length=1, max_length=50)


class InsumoCreate(InsumoBase):
    stock_actual: Decimal = Field(default=Decimal("0"), ge=0)
    stock_minimo: Decimal = Field(default=Decimal("0"), ge=0)
    costo_promedio_actual: Decimal = Field(default=Decimal("0"), ge=0)


class InsumoUpdate(BaseModel):
    categoria_id: int | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    unidad_medida: str | None = Field(default=None, min_length=1, max_length=50)
    stock_actual: Decimal | None = Field(default=None, ge=0)
    stock_minimo: Decimal | None = Field(default=None, ge=0)
    costo_promedio_actual: Decimal | None = Field(default=None, ge=0)


class InsumoRead(InsumoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_actual: Decimal
    stock_minimo: Decimal
    costo_promedio_actual: Decimal
    nombre_categoria: str | None = None