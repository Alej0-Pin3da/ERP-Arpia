"""Maestros schemas — 7 catalogs + singleton."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Proveedor
class ProveedorCreate(BaseModel):
    nombre: str = Field(max_length=100)
    categoria: str = Field(max_length=100)
    ciudad: str | None = Field(default=None, max_length=80)
    calificacion: Decimal | None = Field(default=None, ge=0, le=5)
    tiempo_entrega_dias: int | None = Field(default=None, ge=0)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=50)
    activo: bool | None = True
    notas: str | None = None


class ProveedorUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=100)
    categoria: str | None = Field(default=None, max_length=100)
    ciudad: str | None = Field(default=None, max_length=80)
    calificacion: Decimal | None = Field(default=None, ge=0, le=5)
    tiempo_entrega_dias: int | None = Field(default=None, ge=0)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=50)
    activo: bool | None = None
    notas: str | None = None


class ProveedorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    categoria: str
    ciudad: str | None
    calificacion: Decimal | None
    tiempo_entrega_dias: int | None
    email: str | None
    telefono: str | None
    activo: bool
    notas: str | None
    created_at: datetime
    updated_at: datetime


# Categoria
TipoTalla = Literal["CON_TALLAS_ESTANDAR", "SIN_TALLA_MERCH", "TALLA_UNICA"]


class CategoriaCreate(BaseModel):
    nombre: str = Field(max_length=100)
    tipo_talla: TipoTalla
    descripcion: str | None = None
    margen_meta_pct: Decimal | None = Field(default=None, ge=0, le=100)
    total_modelos: int | None = Field(default=0, ge=0)
    activo: bool | None = True


class CategoriaUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=100)
    tipo_talla: TipoTalla | None = None
    descripcion: str | None = None
    margen_meta_pct: Decimal | None = Field(default=None, ge=0, le=100)
    total_modelos: int | None = Field(default=None, ge=0)
    activo: bool | None = None


class CategoriaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    tipo_talla: str
    descripcion: str | None
    margen_meta_pct: Decimal | None
    total_modelos: int
    activo: bool
    created_at: datetime
    updated_at: datetime


# Ubicacion
TipoUbicacion = Literal["ROLLOS_TELAS", "GAVETAS_HERRAJES", "PERCHERO_SHOWROOM", "ACCESORIOS_BODEGA"]


class UbicacionCreate(BaseModel):
    codigo: str = Field(max_length=20, pattern=r"^UB-.*")
    nombre: str = Field(max_length=100)
    tipo: TipoUbicacion
    capacidad: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None
    activo: bool | None = True


class UbicacionUpdate(BaseModel):
    codigo: str | None = Field(default=None, max_length=20, pattern=r"^UB-.*")
    nombre: str | None = Field(default=None, max_length=100)
    tipo: TipoUbicacion | None = None
    capacidad: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None
    activo: bool | None = None


class UbicacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nombre: str
    tipo: str
    capacidad: str | None
    observaciones: str | None
    activo: bool
    created_at: datetime
    updated_at: datetime


# Canal
TipoCanal = Literal["FISICO", "DIGITAL", "EVENTO"]


class CanalCreate(BaseModel):
    codigo: str = Field(max_length=50)
    nombre: str = Field(max_length=100)
    tipo: TipoCanal | None = None
    comision_pct: Decimal | None = Field(default=None, ge=0, le=100)
    costo_fijo_mensual: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = True
    descripcion: str | None = None


class CanalUpdate(BaseModel):
    codigo: str | None = Field(default=None, max_length=50)
    nombre: str | None = Field(default=None, max_length=100)
    tipo: TipoCanal | None = None
    comision_pct: Decimal | None = Field(default=None, ge=0, le=100)
    costo_fijo_mensual: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = None
    descripcion: str | None = None


class CanalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nombre: str
    tipo: str | None
    comision_pct: Decimal | None
    costo_fijo_mensual: Decimal | None
    activo: bool | None
    descripcion: str | None
    created_at: datetime
    updated_at: datetime | None


# Metodo Pago
TipoMetodo = Literal["TRANSFERENCIA", "BILLETERA_DIGITAL", "EFECTIVO", "PASARELA_DATAFONO"]


class MetodoCreate(BaseModel):
    codigo: str = Field(max_length=50)
    nombre: str = Field(max_length=100)
    tipo: TipoMetodo | None = None
    comision_pct: Decimal | None = Field(default=None, ge=0, le=100)
    tiempo_acreditacion: str | None = Field(default=None, max_length=50)
    activo: bool | None = True
    datos_cuenta: str | None = None
    descripcion: str | None = None


class MetodoUpdate(BaseModel):
    codigo: str | None = Field(default=None, max_length=50)
    nombre: str | None = Field(default=None, max_length=100)
    tipo: TipoMetodo | None = None
    comision_pct: Decimal | None = Field(default=None, ge=0, le=100)
    tiempo_acreditacion: str | None = Field(default=None, max_length=50)
    activo: bool | None = None
    datos_cuenta: str | None = None
    descripcion: str | None = None


class MetodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nombre: str
    tipo: str | None
    comision_pct: Decimal | None
    tiempo_acreditacion: str | None
    activo: bool | None
    datos_cuenta: str | None
    descripcion: str | None
    created_at: datetime
    updated_at: datetime | None


# Talla
class TallaCreate(BaseModel):
    talla: str = Field(max_length=20)
    orden: int
    busto: str | None = Field(default=None, max_length=50)
    cintura: str | None = Field(default=None, max_length=50)
    cadera: str | None = Field(default=None, max_length=50)
    reduccion_corset: str | None = Field(default=None, max_length=50)
    descripcion: str | None = None
    activo: bool | None = True


class TallaUpdate(BaseModel):
    talla: str | None = Field(default=None, max_length=20)
    orden: int | None = None
    busto: str | None = Field(default=None, max_length=50)
    cintura: str | None = Field(default=None, max_length=50)
    cadera: str | None = Field(default=None, max_length=50)
    reduccion_corset: str | None = Field(default=None, max_length=50)
    descripcion: str | None = None
    activo: bool | None = None


class TallaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    talla: str
    orden: int
    busto: str | None
    cintura: str | None
    cadera: str | None
    reduccion_corset: str | None
    descripcion: str | None
    activo: bool
    created_at: datetime
    updated_at: datetime


# Producto sin talla
class ProductoSinTallaCreate(BaseModel):
    nombre: str = Field(max_length=100)
    categoria: str = Field(max_length=100)
    dimensiones: str | None = Field(default=None, max_length=100)
    materiales: str | None = Field(default=None, max_length=200)
    descripcion: str | None = None
    precio_sugerido: Decimal = Field(ge=0)
    activo: bool | None = True


class ProductoSinTallaUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=100)
    categoria: str | None = Field(default=None, max_length=100)
    dimensiones: str | None = Field(default=None, max_length=100)
    materiales: str | None = Field(default=None, max_length=200)
    descripcion: str | None = None
    precio_sugerido: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = None


class ProductoSinTallaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    categoria: str
    dimensiones: str | None
    materiales: str | None
    descripcion: str | None
    precio_sugerido: Decimal
    activo: bool
    created_at: datetime
    updated_at: datetime


# Parametros singleton
class ParametrosRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    costo_minuto_costura: Decimal
    costo_hora_patronaje: Decimal
    margen_meta_global_pct: Decimal
    desperdicio_textil_default_pct: Decimal
    iva_regimen_pct: Decimal
    distribucion_reinversion_pct: Decimal
    reparto_margara_pct: Decimal
    reparto_valqui_pct: Decimal
    created_at: datetime
    updated_at: datetime


class ParametrosUpdate(BaseModel):
    costo_minuto_costura: Decimal | None = Field(default=None, ge=0)
    costo_hora_patronaje: Decimal | None = Field(default=None, ge=0)
    margen_meta_global_pct: Decimal | None = Field(default=None, ge=0, le=100)
    desperdicio_textil_default_pct: Decimal | None = Field(default=None, ge=0, le=100)
    iva_regimen_pct: Decimal | None = Field(default=None, ge=0, le=100)
    distribucion_reinversion_pct: Decimal | None = Field(default=None, ge=0, le=100)
    reparto_margara_pct: Decimal | None = Field(default=None, ge=0, le=100)
    reparto_valqui_pct: Decimal | None = Field(default=None, ge=0, le=100)
