"""Pydantic schemas for the finanzas API surface.

Shape validation only: the sum-to-100 invariant and one-time-settlement rules
live in ``app.services.finanzas`` (the DB cannot express the multi-row
invariant as a CHECK constraint).

Two families coexist:
- Legacy FIN-1/FIN-2: ``MovimientoFinanciero`` and ``SociosConfiguracion`` CRUD
  (the one-time settlement schema is ``LiquidacionSettlementCreate``).
- v4 (PR2): extended socia profile (SOC-1/SOC-2), real ``liquidaciones``
  header+distribution (LIQ-1/2/3) and ``anticipos`` (ANT-1/2/3). These carry
  Literal state values and EmailStr/length validators at the schema layer; the
  sum-to-100, drift>5% and FOR UPDATE rules live in the service layer.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MovimientoCreate(BaseModel):
    tipo: Literal["Gasto", "Inversion", "Retiro"]
    descripcion: str = Field(min_length=1, max_length=500)
    monto: Decimal = Field(gt=0)
    socio_id: int | None = None


class MovimientoUpdate(BaseModel):
    """PATCH body for /finanzas/movimientos/{id} (FIN-1).

    Every field is optional; only the fields actually sent are applied
    (the route passes ``model_dump(exclude_unset=True)``). The liquidation
    guard for monto/socio_id lives in the service (FIN-2).
    """

    fecha: datetime | None = None
    tipo: Literal["Gasto", "Inversion", "Retiro"] | None = None
    descripcion: str | None = Field(default=None, min_length=1, max_length=500)
    monto: Decimal | None = Field(default=None, gt=0)
    socio_id: int | None = None


class MovimientoStateTransition(BaseModel):
    """Schema for document state transitions."""

    estado: Literal["draft", "confirmed", "cancelled", "reversed"]
    motivo: str | None = None


class MovimientoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    tipo: str
    descripcion: str
    monto: Decimal
    socio_id: int | None
    estado: str
    liquidacion_id: str | None
    # Reversal fields
    reversed_motivo: str | None = None
    reversed_by: int | None = None
    reversed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Legacy one-time settlement (FIN-1)
# ---------------------------------------------------------------------------


class LiquidacionSettlementCreate(BaseModel):
    monto: Decimal = Field(gt=0)
    notas: str | None = None
    liquidacion_id: str | None = Field(default=None, max_length=10)


# ---------------------------------------------------------------------------
# SociosConfiguracion — extended profile (SOC-1/SOC-2)
# ---------------------------------------------------------------------------


_TipoCuenta = Literal["AHORROS", "CORRIENTE", "OTRA"]


class SocioConfiguracionCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    porcentaje_participacion: Decimal = Field(gt=0)
    # Extended profile — 10 nullable cols (SOC-1)
    rol: str | None = Field(default=None, max_length=50)
    banco: str | None = Field(default=None, max_length=100)
    es_fondo_taller: bool = False
    telefono: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    tipo_cuenta: _TipoCuenta | None = None
    numero_cuenta: str | None = Field(default=None, max_length=50)
    titular_cuenta: str | None = Field(default=None, max_length=150)
    activo: bool = True
    notas: str | None = None


class SocioConfiguracionUpdate(BaseModel):
    """Partial socia update (SOC-1 PATCH): all fields optional, applied only
    when sent (route passes ``model_dump(exclude_unset=True)``)."""

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    porcentaje_participacion: Decimal | None = Field(default=None, gt=0)
    rol: str | None = Field(default=None, max_length=50)
    banco: str | None = Field(default=None, max_length=100)
    es_fondo_taller: bool | None = None
    telefono: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    tipo_cuenta: _TipoCuenta | None = None
    numero_cuenta: str | None = Field(default=None, max_length=50)
    titular_cuenta: str | None = Field(default=None, max_length=150)
    activo: bool | None = None
    notas: str | None = None


class SocioConfiguracionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    porcentaje_participacion: Decimal
    rol: str | None = None
    banco: str | None = None
    es_fondo_taller: bool | None = None
    telefono: str | None = None
    email: str | None = None
    tipo_cuenta: str | None = None
    numero_cuenta: str | None = None
    titular_cuenta: str | None = None
    activo: bool | None = None
    notas: str | None = None


# ---------------------------------------------------------------------------
# Liquidaciones (LIQ-1/2/3)
# ---------------------------------------------------------------------------


class LiquidacionCreate(BaseModel):
    """Header payload — the six totals plus period/close date (LIQ-1)."""

    periodo: str = Field(min_length=1, max_length=20)
    fecha_cierre: date
    total_ventas_brutas: Decimal
    costo_taller_insumos: Decimal
    gastos_operativos: Decimal
    utilidad_neta_total: Decimal
    fondo_reinversion_monto: Decimal
    utilidad_repartible: Decimal
    observaciones: str | None = None


class LiquidacionEstadoUpdate(BaseModel):
    """State transition body (LIQ-2): only the two linear hops are valid."""

    estado: Literal["BORRADOR", "APROBADA", "PAGADA"]


class LiquidacionDistribucionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    liquidacion_id: int
    socia_id: int
    socia_nombre: str | None = None
    porcentaje: Decimal
    monto_bruto: Decimal
    deduccion_anticipos: Decimal
    monto_neto: Decimal
    estado_pago: str


class LiquidacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    periodo: str
    fecha_cierre: date
    total_ventas_brutas: Decimal
    costo_taller_insumos: Decimal
    gastos_operativos: Decimal
    utilidad_neta_total: Decimal
    fondo_reinversion_monto: Decimal
    utilidad_repartible: Decimal
    estado: str
    observaciones: str | None = None
    distribucion: list[LiquidacionDistribucionRead] = []
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Anticipos (ANT-1/2/3)
# ---------------------------------------------------------------------------


class AnticipoCreate(BaseModel):
    socia_id: int
    monto: Decimal = Field(gt=0)
    fecha: date | None = None
    concepto: str | None = Field(default=None, max_length=255)
    metodo_desembolso: str | None = Field(default=None, max_length=50)
    comprobante: str | None = Field(default=None, max_length=255)
    observaciones: str | None = None


class AnticipoEstadoUpdate(BaseModel):
    """State transition body (ANT-2): PENDIENTE_DESCUENTO -> DESCONTADO|ANULADO."""

    estado: Literal["PENDIENTE_DESCUENTO", "DESCONTADO", "ANULADO"]


class AnticipoDescuentoUpdate(BaseModel):
    """Linking an anticipo to a liquidacion (ANT-2) — atomic set liquidacion_id
    + transition to DESCONTADO."""

    liquidacion_id: int


class AnticipoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    socia_id: int
    socia_nombre: str | None = None
    liquidacion_id: int | None = None
    monto: Decimal
    fecha: date
    estado: str
    concepto: str | None = None
    metodo_desembolso: str | None = None
    comprobante: str | None = None
    observaciones: str | None = None
    creado_en: datetime | None = None
