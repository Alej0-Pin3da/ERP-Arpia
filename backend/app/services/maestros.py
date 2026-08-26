"""Maestros services — CRUD per domain + singleton FOR UPDATE."""
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.maestros import (
    CanalVentaMaestro,
    CategoriaColeccion,
    MetodoPagoMaestro,
    ParametrosCosteo,
    ProductoSinTalla,
    ProveedorMaestro,
    TallaEstandar,
    UbicacionTaller,
)


def _raise_dup(detail: str = "Duplicado"):
    raise HTTPException(status_code=409, detail=detail)


# Generic helpers
def _create(db: Session, instance):
    db.add(instance)
    try:
        db.commit()
        db.refresh(instance)
        return instance
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig) if hasattr(e, "orig") else str(e)
        if "unique" in msg.lower() or "duplicate" in msg.lower():
            _raise_dup(f"Recurso duplicado: {msg}")
        raise HTTPException(status_code=409, detail="Conflicto de integridad") from None
    except Exception:
        db.rollback()
        raise


def _update(db: Session, instance, data: dict):
    for k, v in data.items():
        setattr(instance, k, v)
    try:
        db.commit()
        db.refresh(instance)
        return instance
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig) if hasattr(e, "orig") else str(e)
        _raise_dup(f"Recurso duplicado: {msg}")
    except Exception:
        db.rollback()
        raise


# Proveedor
def crear_proveedor(db: Session, payload: dict) -> ProveedorMaestro:
    # trim/normalize nombre for duplicate check case-insensitive? DB unique is case-sensitive; we rely on DB 409
    return _create(db, ProveedorMaestro(**payload))


def actualizar_proveedor(db: Session, pid: int, data: dict) -> ProveedorMaestro:
    obj = db.get(ProveedorMaestro, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return _update(db, obj, data)


def eliminar_proveedor(db: Session, pid: int) -> None:
    obj = db.get(ProveedorMaestro, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    db.delete(obj)
    db.commit()


# Categoria
def crear_categoria(db: Session, payload: dict) -> CategoriaColeccion:
    return _create(db, CategoriaColeccion(**payload))


def actualizar_categoria(db: Session, cid: int, data: dict) -> CategoriaColeccion:
    obj = db.get(CategoriaColeccion, cid)
    if not obj:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    return _update(db, obj, data)


def eliminar_categoria(db: Session, cid: int) -> None:
    obj = db.get(CategoriaColeccion, cid)
    if not obj:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    db.delete(obj)
    db.commit()


# Ubicacion
def crear_ubicacion(db: Session, payload: dict) -> UbicacionTaller:
    return _create(db, UbicacionTaller(**payload))


def actualizar_ubicacion(db: Session, uid: int, data: dict) -> UbicacionTaller:
    obj = db.get(UbicacionTaller, uid)
    if not obj:
        raise HTTPException(status_code=404, detail="Ubicacion no encontrada")
    return _update(db, obj, data)


def eliminar_ubicacion(db: Session, uid: int) -> None:
    obj = db.get(UbicacionTaller, uid)
    if not obj:
        raise HTTPException(status_code=404, detail="Ubicacion no encontrada")
    db.delete(obj)
    db.commit()


# Canal
def crear_canal(db: Session, payload: dict) -> CanalVentaMaestro:
    return _create(db, CanalVentaMaestro(**payload))


def actualizar_canal(db: Session, cid: int, data: dict) -> CanalVentaMaestro:
    obj = db.get(CanalVentaMaestro, cid)
    if not obj:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    return _update(db, obj, data)


def eliminar_canal(db: Session, cid: int) -> None:
    obj = db.get(CanalVentaMaestro, cid)
    if not obj:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    db.delete(obj)
    db.commit()


# Metodo
def crear_metodo(db: Session, payload: dict) -> MetodoPagoMaestro:
    return _create(db, MetodoPagoMaestro(**payload))


def actualizar_metodo(db: Session, mid: int, data: dict) -> MetodoPagoMaestro:
    obj = db.get(MetodoPagoMaestro, mid)
    if not obj:
        raise HTTPException(status_code=404, detail="Metodo no encontrado")
    return _update(db, obj, data)


def eliminar_metodo(db: Session, mid: int) -> None:
    obj = db.get(MetodoPagoMaestro, mid)
    if not obj:
        raise HTTPException(status_code=404, detail="Metodo no encontrado")
    db.delete(obj)
    db.commit()


# Talla
def crear_talla(db: Session, payload: dict) -> TallaEstandar:
    return _create(db, TallaEstandar(**payload))


def actualizar_talla(db: Session, tid: int, data: dict) -> TallaEstandar:
    obj = db.get(TallaEstandar, tid)
    if not obj:
        raise HTTPException(status_code=404, detail="Talla no encontrada")
    return _update(db, obj, data)


def eliminar_talla(db: Session, tid: int) -> None:
    obj = db.get(TallaEstandar, tid)
    if not obj:
        raise HTTPException(status_code=404, detail="Talla no encontrada")
    db.delete(obj)
    db.commit()


# Producto sin talla
def crear_producto_sin_talla(db: Session, payload: dict) -> ProductoSinTalla:
    return _create(db, ProductoSinTalla(**payload))


def actualizar_producto_sin_talla(db: Session, pid: int, data: dict) -> ProductoSinTalla:
    obj = db.get(ProductoSinTalla, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _update(db, obj, data)


def eliminar_producto_sin_talla(db: Session, pid: int) -> None:
    obj = db.get(ProductoSinTalla, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(obj)
    db.commit()


# Parametros singleton
def get_or_create_parametros(db: Session) -> ParametrosCosteo:
    obj = db.get(ParametrosCosteo, 1)
    if obj:
        return obj
    # auto-create default singleton
    obj = ParametrosCosteo(
        id=1,
        costo_minuto_costura=Decimal("80"),
        costo_hora_patronaje=Decimal("15000"),
        margen_meta_global_pct=Decimal("35"),
        desperdicio_textil_default_pct=Decimal("8"),
        iva_regimen_pct=Decimal("19"),
        distribucion_reinversion_pct=Decimal("40"),
        reparto_margara_pct=Decimal("30"),
        reparto_valqui_pct=Decimal("30"),
    )
    db.add(obj)
    try:
        db.commit()
        db.refresh(obj)
        return obj
    except IntegrityError:
        db.rollback()
        # race: another transaction created it
        obj2 = db.get(ParametrosCosteo, 1)
        if obj2:
            return obj2
        raise


def patch_parametros(db: Session, data: dict) -> ParametrosCosteo:
    # SELECT FOR UPDATE to serialize concurrent patches
    obj = db.execute(select(ParametrosCosteo).where(ParametrosCosteo.id == 1).with_for_update()).scalar_one_or_none()
    if not obj:
        obj = get_or_create_parametros(db)
        obj = db.execute(select(ParametrosCosteo).where(ParametrosCosteo.id == 1).with_for_update()).scalar_one()
    # apply partial updates for validation
    pending = {
        "distribucion_reinversion_pct": obj.distribucion_reinversion_pct,
        "reparto_margara_pct": obj.reparto_margara_pct,
        "reparto_valqui_pct": obj.reparto_valqui_pct,
    }
    for k in ["distribucion_reinversion_pct", "reparto_margara_pct", "reparto_valqui_pct"]:
        if k in data and data[k] is not None:
            pending[k] = Decimal(str(data[k]))
    s = sum(pending.values())
    if abs(s - Decimal("100")) > Decimal("0.01"):
        raise HTTPException(status_code=422, detail=f"Distribucion debe sumar 100, actual {s}")
    for k, v in data.items():
        if v is not None or k in data:
            setattr(obj, k, v)
    try:
        db.commit()
        db.refresh(obj)
        return obj
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from None
