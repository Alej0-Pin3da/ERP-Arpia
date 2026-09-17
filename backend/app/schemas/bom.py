from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalizar_detalle(v: str | None) -> str | None:
    """Blank piece labels become NULL (same rule as factura in compra_insumo)."""
    if v is None:
        return None
    stripped = v.strip()
    return stripped if stripped else None


class BomInsumoBase(BaseModel):
    insumo_id: int
    variante_id: int | None = None
    cantidad_requerida: Decimal = Field(gt=0)
    porcentaje_desperdicio: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    fases: list[Any] | dict[str, Any] | None = None
    tiempo_estimado_minutos: int | None = Field(default=None, ge=0)
    markup_porcentual: Decimal | None = Field(default=None, ge=0)
    detalle: str | None = Field(default=None, max_length=150)

    @field_validator("detalle", mode="after")
    @classmethod
    def _strip_detalle(cls, v: str | None) -> str | None:
        return _normalizar_detalle(v)


class BomInsumoCreate(BomInsumoBase):
    pass


class BomInsumoUpdate(BaseModel):
    insumo_id: int | None = None
    variante_id: int | None = None
    cantidad_requerida: Decimal | None = Field(default=None, gt=0)
    porcentaje_desperdicio: Decimal | None = Field(default=None, ge=0, le=100)
    fases: list[Any] | dict[str, Any] | None = None
    tiempo_estimado_minutos: int | None = Field(default=None, ge=0)
    markup_porcentual: Decimal | None = Field(default=None, ge=0)
    detalle: str | None = Field(default=None, max_length=150)

    @field_validator("detalle", mode="after")
    @classmethod
    def _strip_detalle(cls, v: str | None) -> str | None:
        return _normalizar_detalle(v)


class BomInsumoRead(BomInsumoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int


class BomProductoBase(BaseModel):
    producto_incluido_id: int
    cantidad: Decimal = Field(gt=0)
    fases: list[Any] | dict[str, Any] | None = None
    tiempo_estimado_minutos: int | None = Field(default=None, ge=0)
    markup_porcentual: Decimal | None = Field(default=None, ge=0)


class BomProductoCreate(BomProductoBase):
    pass


class BomProductoUpdate(BaseModel):
    producto_incluido_id: int | None = None
    cantidad: Decimal | None = Field(default=None, gt=0)
    fases: list[Any] | dict[str, Any] | None = None
    tiempo_estimado_minutos: int | None = Field(default=None, ge=0)
    markup_porcentual: Decimal | None = Field(default=None, ge=0)


class BomProductoRead(BomProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    combo_id: int
