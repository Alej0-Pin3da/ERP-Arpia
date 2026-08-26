"""Maestros catalog models — PR1 Foundation 0014 3+2 tables.

- ProveedorMaestro decoupled from 0008 Proveedores (maestros_proveedores)
- CategoriaColeccion, UbicacionTaller new
- CanalVentaMaestro / MetodoPagoMaestro extend 0010 stubs (nullable ALTER)
Keep each file <400 lines via guards; CHECKs, UNIQUEs, NUMERIC(15,4), TIMESTAMPTZ.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProveedorMaestro(Base):
    """Decoupled from 0008 Proveedores deletion — new table maestros_proveedores."""

    __tablename__ = "maestros_proveedores"
    __table_args__ = (
        CheckConstraint("calificacion IS NULL OR (calificacion >= 0 AND calificacion <= 5)", name="ck_proveedores_calificacion"),
        CheckConstraint("tiempo_entrega_dias IS NULL OR tiempo_entrega_dias >= 0", name="ck_proveedores_tiempo_entrega"),
        UniqueConstraint("nombre", name="uq_proveedores_nombre"),
        Index("ix_proveedores_categoria", "categoria"),
        Index("ix_proveedores_ciudad", "ciudad"),
        Index("ix_proveedores_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    ciudad: Mapped[str | None] = mapped_column(String(80), nullable=True)
    calificacion: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    tiempo_entrega_dias: Mapped[int | None] = mapped_column(nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"), default=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ProveedorMaestro id={self.id} nombre={self.nombre!r}>"


class CategoriaColeccion(Base):
    __tablename__ = "maestros_categorias_coleccion"
    __table_args__ = (
        CheckConstraint("tipo_talla IN ('CON_TALLAS_ESTANDAR','SIN_TALLA_MERCH','TALLA_UNICA')", name="ck_categorias_tipo_talla"),
        CheckConstraint("margen_meta_pct IS NULL OR (margen_meta_pct >= 0 AND margen_meta_pct <= 100)", name="ck_categorias_margen"),
        CheckConstraint("total_modelos >= 0", name="ck_categorias_total_modelos"),
        UniqueConstraint("nombre", name="uq_categorias_nombre"),
        Index("ix_categorias_tipo_talla", "tipo_talla"),
        Index("ix_categorias_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tipo_talla: Mapped[str] = mapped_column(String(30), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    margen_meta_pct: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    total_modelos: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"), default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<CategoriaColeccion id={self.id} nombre={self.nombre!r} tipo={self.tipo_talla!r}>"


class UbicacionTaller(Base):
    __tablename__ = "maestros_ubicaciones_taller"
    __table_args__ = (
        CheckConstraint("codigo LIKE 'UB-%'", name="ck_ubicaciones_codigo_ub"),
        CheckConstraint("tipo IN ('ROLLOS_TELAS','GAVETAS_HERRAJES','PERCHERO_SHOWROOM','ACCESORIOS_BODEGA')", name="ck_ubicaciones_tipo"),
        UniqueConstraint("codigo", name="uq_ubicaciones_codigo"),
        UniqueConstraint("nombre", name="uq_ubicaciones_nombre"),
        Index("ix_ubicaciones_tipo", "tipo"),
        Index("ix_ubicaciones_activo", "activo"),
        Index("ix_ubicaciones_codigo", "codigo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    capacidad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"), default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<UbicacionTaller id={self.id} codigo={self.codigo!r}>"


class CanalVentaMaestro(Base):
    """Extends 0010 stub maestros_canales_venta via ALTER — nullable guards keep reversible."""

    __tablename__ = "maestros_canales_venta"
    __table_args__ = (
        CheckConstraint("tipo IS NULL OR tipo IN ('FISICO','DIGITAL','EVENTO')", name="ck_canales_tipo"),
        CheckConstraint("comision_pct IS NULL OR (comision_pct >= 0 AND comision_pct <= 100)", name="ck_canales_comision"),
        CheckConstraint("costo_fijo_mensual IS NULL OR costo_fijo_mensual >= 0", name="ck_canales_costo"),
        Index("ix_canales_tipo", "tipo"),
        Index("ix_canales_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comision_pct: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    costo_fijo_mensual: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    activo: Mapped[bool | None] = mapped_column(nullable=True, server_default=text("true"), default=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    def __repr__(self) -> str:
        return f"<CanalVentaMaestro id={self.id} codigo={self.codigo!r}>"


class MetodoPagoMaestro(Base):
    """Extends 0010 stub maestros_metodos_pago via ALTER — nullable guards keep reversible."""

    __tablename__ = "maestros_metodos_pago"
    __table_args__ = (
        CheckConstraint("tipo IS NULL OR tipo IN ('TRANSFERENCIA','BILLETERA_DIGITAL','EFECTIVO','PASARELA_DATAFONO')", name="ck_metodos_tipo"),
        CheckConstraint("comision_pct IS NULL OR (comision_pct >= 0 AND comision_pct <= 100)", name="ck_metodos_comision"),
        Index("ix_metodos_tipo", "tipo"),
        Index("ix_metodos_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    comision_pct: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    tiempo_acreditacion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activo: Mapped[bool | None] = mapped_column(nullable=True, server_default=text("true"), default=True)
    datos_cuenta: Mapped[str | None] = mapped_column(Text, nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    def __repr__(self) -> str:
        return f"<MetodoPagoMaestro id={self.id} codigo={self.codigo!r}>"


class TallaEstandar(Base):
    """Maestros Tallas Estandar matrix — XXS-XL flat."""

    __tablename__ = "maestros_tallas_estandar"
    __table_args__ = (
        UniqueConstraint("talla", name="uq_tallas_talla"),
        UniqueConstraint("orden", name="uq_tallas_orden"),
        Index("ix_tallas_orden", "orden"),
        Index("ix_tallas_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    talla: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    orden: Mapped[int] = mapped_column(unique=True, nullable=False)
    busto: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cintura: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cadera: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reduccion_corset: Mapped[str | None] = mapped_column(String(50), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"), default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<TallaEstandar id={self.id} talla={self.talla!r}>"


class ProductoSinTalla(Base):
    """Maestros productos sin talla / merch."""

    __tablename__ = "maestros_productos_sin_talla"
    __table_args__ = (
        CheckConstraint("precio_sugerido >= 0", name="ck_sintalla_precio"),
        UniqueConstraint("nombre", name="uq_sintalla_nombre"),
        Index("ix_sintalla_categoria", "categoria"),
        Index("ix_sintalla_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    dimensiones: Mapped[str | None] = mapped_column(String(100), nullable=True)
    materiales: Mapped[str | None] = mapped_column(String(200), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio_sugerido: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("0"), default=Decimal("0"))
    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"), default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ProductoSinTalla id={self.id} nombre={self.nombre!r}>"


class ParametrosCosteo(Base):
    """Singleton row id=1 — costeo global."""

    __tablename__ = "maestros_parametros_costeo"
    __table_args__ = (
        CheckConstraint("costo_minuto_costura >= 0", name="ck_param_minuto"),
        CheckConstraint("costo_hora_patronaje >= 0", name="ck_param_patronaje"),
        CheckConstraint("margen_meta_global_pct >= 0 AND margen_meta_global_pct <= 100", name="ck_param_margen"),
        CheckConstraint("desperdicio_textil_default_pct >= 0 AND desperdicio_textil_default_pct <= 100", name="ck_param_desperdicio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    costo_minuto_costura: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("0"), default=Decimal("0"))
    costo_hora_patronaje: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("0"), default=Decimal("0"))
    margen_meta_global_pct: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("0"), default=Decimal("0"))
    desperdicio_textil_default_pct: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("0"), default=Decimal("0"))
    iva_regimen_pct: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("0"), default=Decimal("0"))
    distribucion_reinversion_pct: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("40"), default=Decimal("40"))
    reparto_margara_pct: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("30"), default=Decimal("30"))
    reparto_valqui_pct: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default=text("30"), default=Decimal("30"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ParametrosCosteo id={self.id}>"
