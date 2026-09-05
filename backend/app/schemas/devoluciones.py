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


class DevolucionStateTransition(BaseModel):
    """Schema for document state transitions."""

    estado: Literal["draft", "confirmed", "cancelled", "reversed"]
    motivo: str | None = None


class DevolucionUpdate(BaseModel):
    """Edit a devolucion: motivo is free text; estado (optional) must follow
    the DocumentState FSM (draft -> confirmed|cancelled, confirmed ->
    cancelled|reversed, cancelled -> reversed, reversed terminal). Only
    draft devoluciones accept motivo edits without restriction; confirmed /
    cancelled accept motivo corrections; reversed is immutable."""

    motivo: str | None = None
    estado: Literal["draft", "confirmed", "cancelled", "reversed"] | None = None


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
    estado: str
    usuario_id: int | None
    items: list[DevolucionItemRead]
    # Reversal fields
    reversed_motivo: str | None = None
    reversed_by: int | None = None
    reversed_at: datetime | None = None
    # Venta reference (resolved by the route mapper, not stored).
    cliente_nombre: str | None = None
    prenda_nombre: str | None = None
