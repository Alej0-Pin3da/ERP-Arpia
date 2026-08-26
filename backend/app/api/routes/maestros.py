"""Maestros API — 7 catalogs + singleton parametros_costeo."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, require_roles
from app.core.limiter import user_limiter
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
from app.schemas.common import Paginated
from app.schemas.maestros import (
    CanalCreate,
    CanalRead,
    CanalUpdate,
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
    MetodoCreate,
    MetodoRead,
    MetodoUpdate,
    ParametrosRead,
    ParametrosUpdate,
    ProductoSinTallaCreate,
    ProductoSinTallaRead,
    ProductoSinTallaUpdate,
    ProveedorCreate,
    ProveedorRead,
    ProveedorUpdate,
    TallaCreate,
    TallaRead,
    TallaUpdate,
    UbicacionCreate,
    UbicacionRead,
    UbicacionUpdate,
)
from app.services.maestros import (
    actualizar_canal,
    actualizar_categoria,
    actualizar_metodo,
    actualizar_producto_sin_talla,
    actualizar_proveedor,
    actualizar_talla,
    actualizar_ubicacion,
    crear_canal,
    crear_categoria,
    crear_metodo,
    crear_producto_sin_talla,
    crear_proveedor,
    crear_talla,
    crear_ubicacion,
    eliminar_canal,
    eliminar_categoria,
    eliminar_metodo,
    eliminar_producto_sin_talla,
    eliminar_proveedor,
    eliminar_talla,
    eliminar_ubicacion,
    get_or_create_parametros,
    patch_parametros,
)
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/maestros", tags=["maestros"])

_critical_limiter = user_limiter if settings.ENVIRONMENT != "test" else Limiter(key_func=lambda r: "test", enabled=False)
mutation_user = require_roles("admin", "operador")
audited_user = require_roles("admin", "operador", "consulta")

_SORT_PROV = {"id": ProveedorMaestro.id, "nombre": ProveedorMaestro.nombre, "categoria": ProveedorMaestro.categoria}
_SORT_CAT = {"id": CategoriaColeccion.id, "nombre": CategoriaColeccion.nombre, "tipo_talla": CategoriaColeccion.tipo_talla}
_SORT_UB = {"id": UbicacionTaller.id, "codigo": UbicacionTaller.codigo, "nombre": UbicacionTaller.nombre, "tipo": UbicacionTaller.tipo}
_SORT_CANAL = {"id": CanalVentaMaestro.id, "nombre": CanalVentaMaestro.nombre, "tipo": CanalVentaMaestro.tipo}
_SORT_MET = {"id": MetodoPagoMaestro.id, "nombre": MetodoPagoMaestro.nombre, "tipo": MetodoPagoMaestro.tipo}
_SORT_TALLA = {"id": TallaEstandar.id, "orden": TallaEstandar.orden, "talla": TallaEstandar.talla}
_SORT_SINT = {"id": ProductoSinTalla.id, "nombre": ProductoSinTalla.nombre, "categoria": ProductoSinTalla.categoria}


# Proveedores
@router.get("/proveedores", response_model=Paginated[ProveedorRead])
def list_proveedores(
    q: str | None = None, categoria: str | None = None, ciudad: str | None = None, activo: bool | None = None,
    limit: int = 50, offset: int = 0, sort_by: str | None = None, order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db), _: object = Depends(audited_user),
):
    stmt = select(ProveedorMaestro).order_by(ProveedorMaestro.id.asc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(ProveedorMaestro.nombre.ilike(like) | ProveedorMaestro.categoria.ilike(like))
    if categoria:
        stmt = stmt.where(ProveedorMaestro.categoria == categoria)
    if ciudad:
        stmt = stmt.where(ProveedorMaestro.ciudad == ciudad)
    if activo is not None:
        stmt = stmt.where(ProveedorMaestro.activo == activo)
    stmt = aplicar_orden(stmt, sort_by, order, _SORT_PROV)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[ProveedorRead](items=rows, total=total)


@router.post("/proveedores", response_model=ProveedorRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_proveedor(request: Request, payload: ProveedorCreate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    obj = crear_proveedor(db, payload.model_dump())
    return obj


@router.get("/proveedores/{pid}", response_model=ProveedorRead)
def get_proveedor(pid: int, db: Session = Depends(get_db), _: object = Depends(audited_user)):
    obj = db.get(ProveedorMaestro, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return obj


@router.patch("/proveedores/{pid}", response_model=ProveedorRead)
@_critical_limiter.limit("30/minute")
def patch_proveedor(request: Request, pid: int, payload: ProveedorUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    obj = actualizar_proveedor(db, pid, payload.model_dump(exclude_unset=True))
    return obj


@router.delete("/proveedores/{pid}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_proveedor(request: Request, pid: int, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    eliminar_proveedor(db, pid)


# Categorias
@router.get("/categorias-coleccion", response_model=Paginated[CategoriaRead])
def list_categorias(q: str | None = None, tipo_talla: str | None = None, activo: bool | None = None, limit: int = 50, offset: int = 0, sort_by: str | None = None, order: Literal["asc", "desc"] = "asc", db: Session = Depends(get_db), _: object = Depends(audited_user)):
    stmt = select(CategoriaColeccion).order_by(CategoriaColeccion.id.asc())
    if q:
        stmt = stmt.where(CategoriaColeccion.nombre.ilike(f"%{q}%"))
    if tipo_talla:
        stmt = stmt.where(CategoriaColeccion.tipo_talla == tipo_talla)
    if activo is not None:
        stmt = stmt.where(CategoriaColeccion.activo == activo)
    stmt = aplicar_orden(stmt, sort_by, order, _SORT_CAT)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[CategoriaRead](items=rows, total=total)


@router.post("/categorias-coleccion", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_categoria(request: Request, payload: CategoriaCreate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return crear_categoria(db, payload.model_dump())


@router.get("/categorias-coleccion/{cid}", response_model=CategoriaRead)
def get_categoria(cid: int, db: Session = Depends(get_db), _: object = Depends(audited_user)):
    obj = db.get(CategoriaColeccion, cid)
    if not obj:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    return obj


@router.patch("/categorias-coleccion/{cid}", response_model=CategoriaRead)
@_critical_limiter.limit("30/minute")
def patch_categoria(request: Request, cid: int, payload: CategoriaUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return actualizar_categoria(db, cid, payload.model_dump(exclude_unset=True))


@router.delete("/categorias-coleccion/{cid}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_categoria(request: Request, cid: int, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    eliminar_categoria(db, cid)


# Ubicaciones
@router.get("/ubicaciones-taller", response_model=Paginated[UbicacionRead])
def list_ubicaciones(q: str | None = None, tipo: str | None = None, activo: bool | None = None, limit: int = 50, offset: int = 0, sort_by: str | None = None, order: Literal["asc", "desc"] = "asc", db: Session = Depends(get_db), _: object = Depends(audited_user)):
    stmt = select(UbicacionTaller).order_by(UbicacionTaller.id.asc())
    if q:
        stmt = stmt.where(UbicacionTaller.nombre.ilike(f"%{q}%") | UbicacionTaller.codigo.ilike(f"%{q}%"))
    if tipo:
        stmt = stmt.where(UbicacionTaller.tipo == tipo)
    if activo is not None:
        stmt = stmt.where(UbicacionTaller.activo == activo)
    stmt = aplicar_orden(stmt, sort_by, order, _SORT_UB)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[UbicacionRead](items=rows, total=total)


@router.post("/ubicaciones-taller", response_model=UbicacionRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_ubicacion(request: Request, payload: UbicacionCreate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return crear_ubicacion(db, payload.model_dump())


@router.get("/ubicaciones-taller/{uid}", response_model=UbicacionRead)
def get_ubicacion(uid: int, db: Session = Depends(get_db), _: object = Depends(audited_user)):
    obj = db.get(UbicacionTaller, uid)
    if not obj:
        raise HTTPException(status_code=404, detail="Ubicacion no encontrada")
    return obj


@router.patch("/ubicaciones-taller/{uid}", response_model=UbicacionRead)
@_critical_limiter.limit("30/minute")
def patch_ubicacion(request: Request, uid: int, payload: UbicacionUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return actualizar_ubicacion(db, uid, payload.model_dump(exclude_unset=True))


@router.delete("/ubicaciones-taller/{uid}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_ubicacion(request: Request, uid: int, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    eliminar_ubicacion(db, uid)


# Canales
@router.get("/canales-venta", response_model=Paginated[CanalRead])
def list_canales(q: str | None = None, tipo: str | None = None, activo: bool | None = None, limit: int = 50, offset: int = 0, sort_by: str | None = None, order: Literal["asc", "desc"] = "asc", db: Session = Depends(get_db), _: object = Depends(audited_user)):
    stmt = select(CanalVentaMaestro).order_by(CanalVentaMaestro.id.asc())
    if q:
        stmt = stmt.where(CanalVentaMaestro.nombre.ilike(f"%{q}%") | CanalVentaMaestro.codigo.ilike(f"%{q}%"))
    if tipo:
        stmt = stmt.where(CanalVentaMaestro.tipo == tipo)
    if activo is not None:
        stmt = stmt.where(CanalVentaMaestro.activo == activo)
    stmt = aplicar_orden(stmt, sort_by, order, _SORT_CANAL)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[CanalRead](items=rows, total=total)


@router.post("/canales-venta", response_model=CanalRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_canal(request: Request, payload: CanalCreate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return crear_canal(db, payload.model_dump())


@router.get("/canales-venta/{cid}", response_model=CanalRead)
def get_canal(cid: int, db: Session = Depends(get_db), _: object = Depends(audited_user)):
    obj = db.get(CanalVentaMaestro, cid)
    if not obj:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    return obj


@router.patch("/canales-venta/{cid}", response_model=CanalRead)
@_critical_limiter.limit("30/minute")
def patch_canal(request: Request, cid: int, payload: CanalUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return actualizar_canal(db, cid, payload.model_dump(exclude_unset=True))


@router.delete("/canales-venta/{cid}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_canal(request: Request, cid: int, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    eliminar_canal(db, cid)


# Metodos pago
@router.get("/metodos-pago", response_model=Paginated[MetodoRead])
def list_metodos(q: str | None = None, tipo: str | None = None, activo: bool | None = None, limit: int = 50, offset: int = 0, sort_by: str | None = None, order: Literal["asc", "desc"] = "asc", db: Session = Depends(get_db), _: object = Depends(audited_user)):
    stmt = select(MetodoPagoMaestro).order_by(MetodoPagoMaestro.id.asc())
    if q:
        stmt = stmt.where(MetodoPagoMaestro.nombre.ilike(f"%{q}%") | MetodoPagoMaestro.codigo.ilike(f"%{q}%"))
    if tipo:
        stmt = stmt.where(MetodoPagoMaestro.tipo == tipo)
    if activo is not None:
        stmt = stmt.where(MetodoPagoMaestro.activo == activo)
    stmt = aplicar_orden(stmt, sort_by, order, _SORT_MET)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[MetodoRead](items=rows, total=total)


@router.post("/metodos-pago", response_model=MetodoRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_metodo(request: Request, payload: MetodoCreate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return crear_metodo(db, payload.model_dump())


@router.get("/metodos-pago/{mid}", response_model=MetodoRead)
def get_metodo(mid: int, db: Session = Depends(get_db), _: object = Depends(audited_user)):
    obj = db.get(MetodoPagoMaestro, mid)
    if not obj:
        raise HTTPException(status_code=404, detail="Metodo no encontrado")
    return obj


@router.patch("/metodos-pago/{mid}", response_model=MetodoRead)
@_critical_limiter.limit("30/minute")
def patch_metodo(request: Request, mid: int, payload: MetodoUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return actualizar_metodo(db, mid, payload.model_dump(exclude_unset=True))


@router.delete("/metodos-pago/{mid}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_metodo(request: Request, mid: int, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    eliminar_metodo(db, mid)


# Tallas
@router.get("/tallas-estandar", response_model=Paginated[TallaRead])
def list_tallas(q: str | None = None, activo: bool | None = None, limit: int = 50, offset: int = 0, sort_by: str | None = None, order: Literal["asc", "desc"] = "asc", db: Session = Depends(get_db), _: object = Depends(audited_user)):
    stmt = select(TallaEstandar).order_by(TallaEstandar.orden.asc())
    if q:
        stmt = stmt.where(TallaEstandar.talla.ilike(f"%{q}%"))
    if activo is not None:
        stmt = stmt.where(TallaEstandar.activo == activo)
    # default orden unless explicit sort_by overrides
    if sort_by:
        stmt = aplicar_orden(select(TallaEstandar), sort_by, order, _SORT_TALLA)
        if q:
            stmt = stmt.where(TallaEstandar.talla.ilike(f"%{q}%"))
        if activo is not None:
            stmt = stmt.where(TallaEstandar.activo == activo)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[TallaRead](items=rows, total=total)


@router.post("/tallas-estandar", response_model=TallaRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_talla(request: Request, payload: TallaCreate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return crear_talla(db, payload.model_dump())


@router.get("/tallas-estandar/{tid}", response_model=TallaRead)
def get_talla(tid: int, db: Session = Depends(get_db), _: object = Depends(audited_user)):
    obj = db.get(TallaEstandar, tid)
    if not obj:
        raise HTTPException(status_code=404, detail="Talla no encontrada")
    return obj


@router.patch("/tallas-estandar/{tid}", response_model=TallaRead)
@_critical_limiter.limit("30/minute")
def patch_talla(request: Request, tid: int, payload: TallaUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return actualizar_talla(db, tid, payload.model_dump(exclude_unset=True))


@router.delete("/tallas-estandar/{tid}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_talla(request: Request, tid: int, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    eliminar_talla(db, tid)


# Productos sin talla
@router.get("/productos-sin-talla", response_model=Paginated[ProductoSinTallaRead])
def list_productos(q: str | None = None, categoria: str | None = None, activo: bool | None = None, limit: int = 50, offset: int = 0, sort_by: str | None = None, order: Literal["asc", "desc"] = "asc", db: Session = Depends(get_db), _: object = Depends(audited_user)):
    stmt = select(ProductoSinTalla).order_by(ProductoSinTalla.id.asc())
    if q:
        stmt = stmt.where(ProductoSinTalla.nombre.ilike(f"%{q}%"))
    if categoria:
        stmt = stmt.where(ProductoSinTalla.categoria == categoria)
    if activo is not None:
        stmt = stmt.where(ProductoSinTalla.activo == activo)
    stmt = aplicar_orden(stmt, sort_by, order, _SORT_SINT)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[ProductoSinTallaRead](items=rows, total=total)


@router.post("/productos-sin-talla", response_model=ProductoSinTallaRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_producto(request: Request, payload: ProductoSinTallaCreate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return crear_producto_sin_talla(db, payload.model_dump())


@router.get("/productos-sin-talla/{pid}", response_model=ProductoSinTallaRead)
def get_producto(pid: int, db: Session = Depends(get_db), _: object = Depends(audited_user)):
    obj = db.get(ProductoSinTalla, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return obj


@router.patch("/productos-sin-talla/{pid}", response_model=ProductoSinTallaRead)
@_critical_limiter.limit("30/minute")
def patch_producto(request: Request, pid: int, payload: ProductoSinTallaUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return actualizar_producto_sin_talla(db, pid, payload.model_dump(exclude_unset=True))


@router.delete("/productos-sin-talla/{pid}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_producto(request: Request, pid: int, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    eliminar_producto_sin_talla(db, pid)


# Parametros singleton
@router.get("/parametros-costeo", response_model=ParametrosRead)
def get_parametros(db: Session = Depends(get_db), _: object = Depends(audited_user)):
    return get_or_create_parametros(db)


@router.patch("/parametros-costeo", response_model=ParametrosRead)
@_critical_limiter.limit("30/minute")
def patch_parametros_route(request: Request, payload: ParametrosUpdate, db: Session = Depends(get_db), _: object = Depends(mutation_user)):
    return patch_parametros(db, payload.model_dump(exclude_unset=True))
