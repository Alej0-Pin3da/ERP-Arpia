from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _check_finite(v: Decimal | None) -> Decimal | None:
    if v is None:
        return v
    # Decimal('Infinity') / Decimal('NaN') are valid Decimal values but must be rejected
    if not v.is_finite():
        raise ValueError("must be finite (Infinity/NaN not allowed)")
    return v


class CompraInsumoCreate(BaseModel):
    insumo_id: int
    proveedor_id: int | None = None
    cantidad_comprada: Decimal = Field(gt=0)
    modo: Literal["TOTAL", "UNIT"] = "UNIT"
    precio_unitario_compra: Decimal | None = Field(default=None, ge=0)
    costo_total: Decimal | None = Field(default=None, gt=0)
    factura: str | None = Field(default=None, max_length=100)

    @field_validator("cantidad_comprada", "precio_unitario_compra", "costo_total", mode="after")
    @classmethod
    def _finite(cls, v: Decimal | None) -> Decimal | None:
        return _check_finite(v)

    @field_validator("factura", mode="after")
    @classmethod
    def _strip_factura(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None

    @model_validator(mode="after")
    def _check_modo_fields(self) -> "CompraInsumoCreate":
        # Ensure finite already checked; now enforce modo semantics
        if self.modo == "UNIT":
            if self.precio_unitario_compra is None:
                raise ValueError("precio_unitario_compra is required when modo is UNIT")
            if self.costo_total is not None:
                raise ValueError("costo_total must not be set when modo is UNIT")
        else:  # TOTAL
            if self.costo_total is None:
                raise ValueError("costo_total is required when modo is TOTAL")
            if self.precio_unitario_compra is not None:
                raise ValueError("precio_unitario_compra must not be set when modo is TOTAL")
        return self


class CompraInsumoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    insumo_id: int
    proveedor_id: int | None = None
    fecha_compra: datetime
    cantidad_comprada: Decimal
    precio_unitario_compra: Decimal
    costo_unitario_aplicado: Decimal | None = None
    factura: str | None = None
