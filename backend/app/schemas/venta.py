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
    # P1-6 (0024): canal/metodo are validated against maestros_canales_venta /
    # maestros_metodos_pago in the service (any active maestro codigo is
    # accepted, not just the 5/4 canonicals) — the DB FK is the hard backstop.
    cliente_id: int | None = None
    canal_venta: str = Field(min_length=1, max_length=50)
    metodo_pago: str | None = Field(default=None, max_length=50)
    descuento_porcentaje: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    es_regalo: bool = False
    detalles: list[DetalleVentaCreate] = Field(min_length=1)


class VentaUpdate(BaseModel):
    es_regalo: bool


class VentaStateTransition(BaseModel):
    """Schema for document state transitions."""

    estado: Literal["draft", "confirmed", "cancelled", "reversed"]
    motivo: str | None = None


class DetalleVentaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    variante_id: int | None
    cantidad: Decimal
    precio_unitario_aplicado: Decimal
    costo_unitario_aplicado: Decimal
    # Enriched descriptive fields (derived from relationships / computed)
    nombre_prenda: str | None = None
    talla: str | None = None
    nombre_variante: str | None = None
    color: str | None = None
    subtotal: Decimal | None = None
    costo_subtotal: Decimal | None = None


class VentaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    cliente_id: int | None
    canal_venta: str
    metodo_pago: str | None = None
    descuento_porcentaje: Decimal
    estado: str
    total_venta: Decimal
    es_regalo: bool
    detalles: list[DetalleVentaRead]
    # Reversal fields
    reversed_motivo: str | None = None
    reversed_by: int | None = None
    reversed_at: datetime | None = None
    # Enriched fields (derived via model @property, no extra query if selectin)
    cliente_nombre: str | None = None
    codigo: str | None = None
    subtotal: Decimal | None = None
    costo_total: Decimal | None = None
    ganancia_neta: Decimal | None = None
    margen_pct: Decimal | None = None
    reinversion_40: Decimal | None = None
    margarita_30: Decimal | None = None
    valqui_30: Decimal | None = None
