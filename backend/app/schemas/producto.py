from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TipoProductoBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)


class TipoProductoCreate(TipoProductoBase):
    pass


class TipoProductoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)


class TipoProductoRead(TipoProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProductoBase(BaseModel):
    tipo_producto_id: int
    nombre: str = Field(min_length=1, max_length=255)
    requiere_fabricacion: bool = True
    costos_operativos_fijos: Decimal = Field(default=Decimal("0"), ge=0)
    precio_venta_sugerido: Decimal = Field(default=Decimal("0"), ge=0)
    codigo: str | None = Field(default=None, max_length=50)
    categoria: str | None = Field(default=None, max_length=100)
    linea: str | None = Field(default=None, max_length=100)
    descripcion: str | None = None
    tiempo_confeccion_min: int | None = Field(default=None, ge=0)
    costo_insumos: Decimal | None = Field(default=None, ge=0)
    mano_obra: Decimal | None = Field(default=None, ge=0)
    cif_energia: Decimal | None = Field(default=None, ge=0)
    markup_pct: Decimal | None = Field(default=None, ge=0, le=100)
    recomendaciones_taller: str | None = None
    fases: list | dict | None = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    tipo_producto_id: int | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    requiere_fabricacion: bool | None = None
    costos_operativos_fijos: Decimal | None = Field(default=None, ge=0)
    precio_venta_sugerido: Decimal | None = Field(default=None, ge=0)
    codigo: str | None = Field(default=None, max_length=50)
    categoria: str | None = Field(default=None, max_length=100)
    linea: str | None = Field(default=None, max_length=100)
    descripcion: str | None = None
    tiempo_confeccion_min: int | None = Field(default=None, ge=0)
    costo_insumos: Decimal | None = Field(default=None, ge=0)
    mano_obra: Decimal | None = Field(default=None, ge=0)
    cif_energia: Decimal | None = Field(default=None, ge=0)
    markup_pct: Decimal | None = Field(default=None, ge=0, le=100)
    recomendaciones_taller: str | None = None
    fases: list | dict | None = None


class ProductoRead(ProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class VarianteProductoBase(BaseModel):
    nombre_variante: str = Field(min_length=1, max_length=150)
    precio_venta: Decimal | None = Field(default=None, ge=0)


class VarianteProductoCreate(VarianteProductoBase):
    pass


class VarianteProductoUpdate(BaseModel):
    nombre_variante: str | None = Field(default=None, min_length=1, max_length=150)
    precio_venta: Decimal | None = Field(default=None, ge=0)


class VarianteProductoRead(VarianteProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
