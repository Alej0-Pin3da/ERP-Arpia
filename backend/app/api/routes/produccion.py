from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_admin, require_roles
from app.models.produccion import (
    PedidoProduccion,
    PedidoProduccionEstado,
    PedidoProduccionPrioridad,
    PrendaConfeccionada,
    PrendaEstado,
)
from app.models.productos import Producto, VarianteProducto
from app.schemas.common import Paginated
from app.schemas.produccion import (
    PedidoProduccionCreate,
    PedidoProduccionRead,
    PedidoProduccionUpdate,
    PrendaConfeccionadaCreate,
    PrendaConfeccionadaRead,
    PrendaConfeccionadaUpdate,
)
from app.services.paginacion import aplicar_orden, paginar

router_prendas = APIRouter(prefix="/prendas-confeccionadas", tags=["prendas-confeccionadas"])
router_pedidos = APIRouter(prefix="/pedidos-produccion", tags=["pedidos-produccion"])

audited_user = require_roles("admin", "operador", "consulta")


# --- Prendas Confeccionadas ---

_SORTABLE_PRENDAS = {
    "id": PrendaConfeccionada.id,
    "talla": PrendaConfeccionada.talla,
    "estado": PrendaConfeccionada.estado,
    "ubicacion": PrendaConfeccionada.ubicacion,
    "costo_real": PrendaConfeccionada.costo_real,
    "precio_venta": PrendaConfeccionada.precio_venta,
    "fecha_confeccion": PrendaConfeccionada.fecha_confeccion,
    "created_at": PrendaConfeccionada.created_at,
}


def _prenda_to_read(prenda: PrendaConfeccionada) -> PrendaConfeccionadaRead:
    res = PrendaConfeccionadaRead.model_validate(prenda)
    if prenda.variante is not None:
        res.nombre_variante = prenda.variante.nombre_variante
        if prenda.variante.producto is not None:
            res.nombre_producto = prenda.variante.producto.nombre
    return res


@router_prendas.get("", response_model=Paginated[PrendaConfeccionadaRead])
def list_prendas(
    limit: int = 50,
    offset: int = 0,
    variante_id: int | None = None,
    estado: str | None = None,
    talla: str | None = None,
    ubicacion: str | None = None,
    pedido_id: int | None = None,
    q: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    _: PrendaConfeccionada = Depends(audited_user),
):
    stmt = (
        select(PrendaConfeccionada)
        .options(
            selectinload(PrendaConfeccionada.variante).selectinload(VarianteProducto.producto),
            selectinload(PrendaConfeccionada.pedido),
        )
        .order_by(PrendaConfeccionada.id.desc())
    )
    if variante_id is not None:
        stmt = stmt.where(PrendaConfeccionada.variante_id == variante_id)
    if estado is not None:
        stmt = stmt.where(PrendaConfeccionada.estado == estado)
    if talla is not None:
        stmt = stmt.where(PrendaConfeccionada.talla == talla)
    if ubicacion is not None:
        stmt = stmt.where(PrendaConfeccionada.ubicacion.ilike(f"%{ubicacion}%"))
    if pedido_id is not None:
        stmt = stmt.where(PrendaConfeccionada.pedido_id == pedido_id)
    if q is not None:
        stmt = stmt.where(
            or_(
                PrendaConfeccionada.talla.ilike(f"%{q}%"),
                PrendaConfeccionada.estado.ilike(f"%{q}%"),
                PrendaConfeccionada.ubicacion.ilike(f"%{q}%"),
            )
        )
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_PRENDAS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[PrendaConfeccionadaRead](
        items=[_prenda_to_read(p) for p in rows], total=total
    )


@router_prendas.get("/{prenda_id}", response_model=PrendaConfeccionadaRead)
def get_prenda(
    prenda_id: int,
    db: Session = Depends(get_db),
    _: PrendaConfeccionada = Depends(audited_user),
):
    prenda = db.get(PrendaConfeccionada, prenda_id)
    if prenda is None:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    return _prenda_to_read(prenda)


@router_prendas.post("", response_model=PrendaConfeccionadaRead, status_code=status.HTTP_201_CREATED)
def create_prenda(
    payload: PrendaConfeccionadaCreate,
    db: Session = Depends(get_db),
    _: PrendaConfeccionada = Depends(require_admin),
):
    # P2-7: variante_id nullable (generic stock); only validate when given.
    if payload.variante_id is not None and db.get(VarianteProducto, payload.variante_id) is None:
        raise HTTPException(status_code=400, detail="Variante de producto no existe")
    if payload.pedido_id is not None and db.get(PedidoProduccion, payload.pedido_id) is None:
        raise HTTPException(status_code=400, detail="Pedido de producción no existe")

    prenda = PrendaConfeccionada(**payload.model_dump())
    db.add(prenda)
    try:
        db.commit()
        db.refresh(prenda)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e

    return _prenda_to_read(prenda)


@router_prendas.patch("/{prenda_id}", response_model=PrendaConfeccionadaRead)
def update_prenda(
    prenda_id: int,
    payload: PrendaConfeccionadaUpdate,
    db: Session = Depends(get_db),
    _: PrendaConfeccionada = Depends(require_admin),
):
    prenda = db.get(PrendaConfeccionada, prenda_id)
    if prenda is None:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")

    if payload.variante_id is not None and db.get(VarianteProducto, payload.variante_id) is None:
        raise HTTPException(status_code=400, detail="Variante de producto no existe")
    if payload.pedido_id is not None and db.get(PedidoProduccion, payload.pedido_id) is None:
        raise HTTPException(status_code=400, detail="Pedido de producción no existe")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(prenda, k, v)

    try:
        db.commit()
        db.refresh(prenda)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e

    return _prenda_to_read(prenda)


# @deprecated: PUT alias — PATCH is the canonical verb for partial updates.
# Kept so existing clients don't break; new code must use PATCH.
@router_prendas.put("/{prenda_id}", response_model=PrendaConfeccionadaRead, deprecated=True)
def update_prenda_put(
    prenda_id: int,
    payload: PrendaConfeccionadaUpdate,
    db: Session = Depends(get_db),
    _admin: PrendaConfeccionada = Depends(require_admin),
):
    return update_prenda(prenda_id, payload, db, _admin)


@router_prendas.delete("/{prenda_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prenda(
    prenda_id: int,
    db: Session = Depends(get_db),
    _: PrendaConfeccionada = Depends(require_admin),
):
    prenda = db.get(PrendaConfeccionada, prenda_id)
    if prenda is None:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    db.delete(prenda)
    db.commit()


# --- Pedidos de Producción ---

_SORTABLE_PEDIDOS = {
    "id": PedidoProduccion.id,
    "cantidad": PedidoProduccion.cantidad,
    "cantidad_producida": PedidoProduccion.cantidad_producida,
    "estado": PedidoProduccion.estado,
    "prioridad": PedidoProduccion.prioridad,
    "fecha_pedido": PedidoProduccion.fecha_pedido,
    "fecha_entrega_estimada": PedidoProduccion.fecha_entrega_estimada,
    "created_at": PedidoProduccion.created_at,
}


def _pedido_to_read(pedido: PedidoProduccion) -> PedidoProduccionRead:
    res = PedidoProduccionRead.model_validate(pedido)
    if pedido.producto is not None:
        res.nombre_producto = pedido.producto.nombre
    if pedido.variante is not None:
        res.nombre_variante = pedido.variante.nombre_variante
    return res


@router_pedidos.get("", response_model=Paginated[PedidoProduccionRead])
def list_pedidos(
    limit: int = 50,
    offset: int = 0,
    producto_id: int | None = None,
    variante_id: int | None = None,
    estado: str | None = None,
    prioridad: str | None = None,
    q: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(audited_user),
):
    stmt = (
        select(PedidoProduccion)
        .options(
            selectinload(PedidoProduccion.producto),
            selectinload(PedidoProduccion.variante),
            selectinload(PedidoProduccion.prendas),
        )
        .order_by(PedidoProduccion.id.desc())
    )
    if producto_id is not None:
        stmt = stmt.where(PedidoProduccion.producto_id == producto_id)
    if variante_id is not None:
        stmt = stmt.where(PedidoProduccion.variante_id == variante_id)
    if estado is not None:
        stmt = stmt.where(PedidoProduccion.estado == estado)
    if prioridad is not None:
        stmt = stmt.where(PedidoProduccion.prioridad == prioridad)
    if q is not None:
        stmt = stmt.where(
            or_(
                PedidoProduccion.estado.ilike(f"%{q}%"),
                PedidoProduccion.prioridad.ilike(f"%{q}%"),
                PedidoProduccion.observaciones.ilike(f"%{q}%"),
            )
        )
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_PEDIDOS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[PedidoProduccionRead](
        items=[_pedido_to_read(p) for p in rows], total=total
    )


@router_pedidos.get("/{pedido_id}", response_model=PedidoProduccionRead)
def get_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(audited_user),
):
    pedido = db.get(PedidoProduccion, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido de producción no encontrado")
    return _pedido_to_read(pedido)


@router_pedidos.post("", response_model=PedidoProduccionRead, status_code=status.HTTP_201_CREATED)
def create_pedido(
    payload: PedidoProduccionCreate,
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(require_admin),
):
    if db.get(Producto, payload.producto_id) is None:
        raise HTTPException(status_code=400, detail="Producto no existe")
    if payload.variante_id is not None and db.get(VarianteProducto, payload.variante_id) is None:
        raise HTTPException(status_code=400, detail="Variante de producto no existe")

    pedido = PedidoProduccion(**payload.model_dump())
    db.add(pedido)
    try:
        db.commit()
        db.refresh(pedido)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e

    return _pedido_to_read(pedido)


@router_pedidos.patch("/{pedido_id}", response_model=PedidoProduccionRead)
def update_pedido(
    pedido_id: int,
    payload: PedidoProduccionUpdate,
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(require_admin),
):
    pedido = db.get(PedidoProduccion, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido de producción no encontrado")

    if payload.producto_id is not None and db.get(Producto, payload.producto_id) is None:
        raise HTTPException(status_code=400, detail="Producto no existe")
    if payload.variante_id is not None and db.get(VarianteProducto, payload.variante_id) is None:
        raise HTTPException(status_code=400, detail="Variante de producto no existe")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(pedido, k, v)

    try:
        db.commit()
        db.refresh(pedido)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e

    return _pedido_to_read(pedido)


# @deprecated: PUT alias — PATCH is the canonical verb for partial updates.
# Kept so existing clients don't break; new code must use PATCH.
@router_pedidos.put("/{pedido_id}", response_model=PedidoProduccionRead, deprecated=True)
def update_pedido_put(
    pedido_id: int,
    payload: PedidoProduccionUpdate,
    db: Session = Depends(get_db),
    _admin: PedidoProduccion = Depends(require_admin),
):
    return update_pedido(pedido_id, payload, db, _admin)


@router_pedidos.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(require_admin),
):
    pedido = db.get(PedidoProduccion, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido de producción no encontrado")
    db.delete(pedido)
    db.commit()
