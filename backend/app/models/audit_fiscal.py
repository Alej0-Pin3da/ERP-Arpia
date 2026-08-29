from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, text
from sqlalchemy.orm import declarative_base
from app.db.base import Base

class PrecioVersion(Base):
    __tablename__ = "precio_versions"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    variante_id = Column(Integer, ForeignKey("variantes_producto.id", ondelete="CASCADE"), nullable=True)
    precio = Column(Numeric(15,4), nullable=False)
    fecha_desde = Column(Date, nullable=False)
    creado_por = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

class CostoVersion(Base):
    __tablename__ = "costo_versions"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    costo = Column(Numeric(15,4), nullable=False)
    fecha_desde = Column(Date, nullable=False)
    creado_por = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

class CierreMensual(Base):
    __tablename__ = "cierres_mensuales"
    id = Column(Integer, primary_key=True)
    periodo = Column(String(7), nullable=False, unique=True)
    estado = Column(String(20), nullable=False, server_default="cerrado")
    cerrado_por = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
