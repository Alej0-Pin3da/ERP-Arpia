from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.produccion import (
    PedidoProduccionEstado,
    PedidoProduccionFase,
    PedidoProduccionPrioridad,
    PrendaEstado,
)


class PrendaConfeccionadaBase(BaseModel):
    # Direct product link (0040): the attribution for generic (talla-less)
    # rows; variant-linked rows resolve through their variant.
    producto_id: int | None = Field(default=None)
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
    producto_id: int | None = None
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
    venta_id: int | None = None
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
    # Workshop phase (lote slice): corte -> costura -> acabados -> calidad -> listo.
    fase: str = Field(default=PedidoProduccionFase.CORTE, max_length=20)
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
    # Workshop phase (lote slice): corte -> costura -> acabados -> calidad -> listo.
    fase: str | None = Field(default=None, max_length=20)
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
    # Unit-cost snapshot taken once at lot completion (None until then).
    costo_unitario_snapshot: Decimal | None = None
    # Real labor/energy cost derived at read time from TiempoFase rows x
    # global rates (mano: all phases; energia: 'costura' only).
    # None when the lot has no tiempos logged yet.
    mano_obra_real: Decimal | None = None
    energia_real: Decimal | None = None
    nombre_producto: str | None = None
    nombre_variante: str | None = None
    cliente_nombre: str | None = None


class TiempoFaseCreate(BaseModel):
    fase: str = Field(max_length=20)
    operaria: str = Field(min_length=1, max_length=150)
    minutos_reales: Decimal = Field(gt=0)
    fecha: date | None = None


class TiempoFaseUpdate(BaseModel):
    operaria: str | None = Field(default=None, min_length=1, max_length=150)
    minutos_reales: Decimal | None = Field(default=None, gt=0)


class TiempoFaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    fase: str
    operaria: str
    minutos_reales: Decimal
    fecha: date
    # Read-time derivation: minutos x global rate (never stored).
    # costo_mano_obra counts every phase; costo_energia only 'costura'.
    costo_mano_obra: Decimal | None = None
    costo_energia: Decimal | None = None


class TiemposListRead(BaseModel):
    items: list[TiempoFaseRead]
    total_minutos: Decimal
    total_mano_obra: Decimal
    total_energia: Decimal
