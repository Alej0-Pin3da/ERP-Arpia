from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BomInsumoBase(BaseModel):
    insumo_id: int
    variante_id: int | None = None
    cantidad_requerida: Decimal = Field(gt=0)
    porcentaje_desperdicio: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class BomInsumoCreate(BomInsumoBase):
    pass


class BomInsumoUpdate(BaseModel):
    insumo_id: int | None = None
    variante_id: int | None = None
    cantidad_requerida: Decimal | None = Field(default=None, gt=0)
    porcentaje_desperdicio: Decimal | None = Field(default=None, ge=0, le=100)


class BomInsumoRead(BomInsumoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int


class BomProductoBase(BaseModel):
    producto_incluido_id: int
    cantidad: Decimal = Field(gt=0)


class BomProductoCreate(BomProductoBase):
    pass


class BomProductoUpdate(BaseModel):
    producto_incluido_id: int | None = None
    cantidad: Decimal | None = Field(default=None, gt=0)


class BomProductoRead(BomProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    combo_id: int
