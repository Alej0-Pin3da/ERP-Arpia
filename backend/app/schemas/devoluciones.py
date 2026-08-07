"""Pydantic schemas for the devoluciones API surface.

Shape validation only: the return business rules (snapshot pricing, qty vs
sold, single-return invariant, atomic restock) live in
``app.services.devoluciones``. ``precio_unitario`` is accepted on the create
payload only to mirror the Venta item shape — the service ALWAYS prices a
return from the sale-time ``precio_unitario_aplicado`` snapshot and ignores the
client value.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DevolucionItemCreate(BaseModel):
    producto_id: int
    variante_id: int | None = None
    cantidad: Decimal = Field(gt=0)
    precio_unitario: Decimal = Field(ge=0)


class DevolucionCreate(BaseModel):
    venta_id: int
    tipo: Literal["total", "parcial"]
    motivo: str | None = None
    # 'total' cancels the whole sale (items optional); 'parcial' requires at
    # least one line (enforced below).
    items: list[DevolucionItemCreate] | None = None

    @model_validator(mode="after")
    def _parcial_requiere_items(self) -> "DevolucionCreate":
        if self.tipo == "parcial" and not self.items:
            raise ValueError("Una devolución parcial debe incluir al menos un item")
        return self


class DevolucionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    variante_id: int | None
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal


class DevolucionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venta_id: int
    fecha: datetime
    motivo: str | None
    monto_reembolsado: Decimal
    tipo: str
    usuario_id: int | None
    items: list[DevolucionItemRead]
