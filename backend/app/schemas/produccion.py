from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.produccion import PedidoProduccionEstado, PedidoProduccionPrioridad, PrendaEstado


class PrendaConfeccionadaBase(BaseModel):
    # P2-7: nullable — allows generic/no-size stock ("Sin talla").
    variante_id: int | None = Field(default=None)
    talla: str | None = Field(default=None, max_length=20)
    estado: str = Field(default=PrendaEstado.DISPONIBLE, max_length=30)
    ubicacion: str | None = Field(default=None, max_length=100)
    costo_real: Decimal | None = Field(default=None, ge=0)
    precio_venta: Decimal | None = Field(default=None, ge=0)
    fecha_confeccion: date | None = None
    pedido_id: int | None = None


class PrendaConfeccionadaCreate(PrendaConfeccionadaBase):
    pass


class PrendaConfeccionadaUpdate(BaseModel):
    variante_id: int | None = None
    talla: str | None = Field(default=None, max_length=20)
    estado: str | None = Field(default=None, max_length=30)
    ubicacion: str | None = Field(default=None, max_length=100)
    costo_real: Decimal | None = Field(default=None, ge=0)
    precio_venta: Decimal | None = Field(default=None, ge=0)
    fecha_confeccion: date | None = None
    pedido_id: int | None = None


class PrendaConfeccionadaRead(PrendaConfeccionadaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    nombre_producto: str | None = None
    nombre_variante: str | None = None


class PedidoProduccionBase(BaseModel):
    producto_id: int
    # Clienta que realiza el pedido (0026, nullable).
    cliente_id: int | None = None
    variante_id: int | None = None
    cantidad: int = Field(gt=0)
    cantidad_producida: int = Field(default=0, ge=0)
    estado: str = Field(default=PedidoProduccionEstado.PENDIENTE, max_length=30)
    prioridad: str = Field(default=PedidoProduccionPrioridad.NORMAL, max_length=20)
    fecha_pedido: date = Field(default_factory=date.today)
    fecha_entrega_estimada: date | None = None
    observaciones: str | None = None


class PedidoProduccionCreate(PedidoProduccionBase):
    pass


class PedidoProduccionUpdate(BaseModel):
    producto_id: int | None = None
    cliente_id: int | None = None
    variante_id: int | None = None
    cantidad: int | None = Field(default=None, gt=0)
    cantidad_producida: int | None = Field(default=None, ge=0)
    estado: str | None = Field(default=None, max_length=30)
    prioridad: str | None = Field(default=None, max_length=20)
    fecha_pedido: date | None = None
    fecha_entrega_estimada: date | None = None
    observaciones: str | None = None


class PedidoProduccionRead(PedidoProduccionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    nombre_producto: str | None = None
    nombre_variante: str | None = None
    cliente_nombre: str | None = None
