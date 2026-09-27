"""Pydantic schemas for the kits API surface.

Money is Decimal everywhere. Read models carry a live cost snapshot
(``costo_total``/``margen_pct``/``alerta_margen``) computed by
``services.kits.costear_kit`` — the margin alert is visual, never a block.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class KitLineaCreate(BaseModel):
    producto_id: int
    cantidad: Decimal = Field(default=Decimal("1"), gt=0)


class KitCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    precio_promocional: Decimal = Field(default=Decimal("0"), ge=0)
    lineas: list[KitLineaCreate] = Field(default_factory=list)


class KitUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    precio_promocional: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = None


class KitLineaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    producto_nombre: str | None = None
    cantidad: Decimal
    costo_unitario: Decimal
    subtotal: Decimal


class KitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    precio_promocional: Decimal
    activo: bool
    costo_total: Decimal
    margen_pct: Decimal
    alerta_margen: bool
    lineas: list[KitLineaRead] = Field(default_factory=list)
