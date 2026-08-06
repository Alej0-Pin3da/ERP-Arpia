from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.productos import Producto, TipoProducto, VarianteProducto
from app.schemas.producto import (
    ProductoCreate,
    ProductoRead,
    ProductoUpdate,
    VarianteProductoCreate,
    VarianteProductoRead,
    VarianteProductoUpdate,
)

router = APIRouter(prefix="/productos", tags=["productos"])

audited_user = require_roles("admin", "operador", "consulta")


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ProductoRead])
def list_productos(
    tipo_producto_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: Producto = Depends(audited_user),
):
    stmt = select(Producto).order_by(Producto.id).limit(limit).offset(offset)
    if tipo_producto_id is not None:
        stmt = stmt.where(Producto.tipo_producto_id == tipo_producto_id)
    return list(db.scalars(stmt).all())


@router.get("/{producto_id}", response_model=ProductoRead)
def get_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(audited_user),
):
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    return producto


@router.post("", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def create_producto(
    payload: ProductoCreate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    if db.get(TipoProducto, payload.tipo_producto_id) is None:
        raise HTTPException(status_code=400, detail="TipoProducto does not exist")
    producto = Producto(**payload.model_dump())
    db.add(producto)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Producto conflicts with existing data"
        )
    db.refresh(producto)
    return producto


@router.put("/{producto_id}", response_model=ProductoRead)
def update_producto(
    producto_id: int,
    payload: ProductoUpdate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    if (
        payload.tipo_producto_id is not None
        and db.get(TipoProducto, payload.tipo_producto_id) is None
    ):
        raise HTTPException(status_code=400, detail="TipoProducto does not exist")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(producto, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Producto conflicts with existing data"
        )
    db.refresh(producto)
    return producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    db.delete(producto)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Producto is in use and cannot be deleted"
        )


# ---------------------------------------------------------------------------
# Variantes_Producto (nested under /productos/{producto_id}/variantes)
# ---------------------------------------------------------------------------


@router.get(
    "/{producto_id}/variantes", response_model=list[VarianteProductoRead]
)
def list_variantes(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(audited_user),
):
    if db.get(Producto, producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    stmt = (
        select(VarianteProducto)
        .where(VarianteProducto.producto_id == producto_id)
        .order_by(VarianteProducto.id)
    )
    return list(db.scalars(stmt).all())


@router.post(
    "/{producto_id}/variantes",
    response_model=VarianteProductoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_variante(
    producto_id: int,
    payload: VarianteProductoCreate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    if db.get(Producto, producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    variante = VarianteProducto(producto_id=producto_id, **payload.model_dump())
    db.add(variante)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="VarianteProducto name already exists for this product",
        )
    db.refresh(variante)
    return variante


@router.put(
    "/{producto_id}/variantes/{variante_id}", response_model=VarianteProductoRead
)
def update_variante(
    producto_id: int,
    variante_id: int,
    payload: VarianteProductoUpdate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    if db.get(Producto, producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    variante = db.get(VarianteProducto, variante_id)
    if variante is None or variante.producto_id != producto_id:
        raise HTTPException(status_code=404, detail="VarianteProducto not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(variante, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="VarianteProducto name already exists for this product",
        )
    db.refresh(variante)
    return variante


@router.delete(
    "/{producto_id}/variantes/{variante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_variante(
    producto_id: int,
    variante_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    if db.get(Producto, producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    variante = db.get(VarianteProducto, variante_id)
    if variante is None or variante.producto_id != producto_id:
        raise HTTPException(status_code=404, detail="VarianteProducto not found")
    db.delete(variante)
    db.commit()
