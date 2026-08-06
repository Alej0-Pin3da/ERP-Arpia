from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.insumos import Insumo
from app.models.productos import BomInsumo, BomProducto, Producto, VarianteProducto
from app.schemas.bom import (
    BomInsumoCreate,
    BomInsumoRead,
    BomInsumoUpdate,
    BomProductoCreate,
    BomProductoRead,
    BomProductoUpdate,
)

router = APIRouter(prefix="/productos", tags=["bom"])

audited_user = require_roles("admin", "operador", "consulta")


def _get_producto_or_404(db: Session, producto_id: int) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto not found")
    return producto


def _validar_variante_del_producto(
    db: Session, producto_id: int, variante_id: int
) -> None:
    variante = db.get(VarianteProducto, variante_id)
    if variante is None or variante.producto_id != producto_id:
        raise HTTPException(
            status_code=400,
            detail="VarianteProducto does not belong to this product",
        )


def validar_linea_insumo_unica(
    db: Session,
    producto_id: int,
    insumo_id: int,
    variante_id: int | None,
    exclude_id: int | None = None,
) -> None:
    """Reject duplicate BOM insumo lines.

    PostgreSQL treats NULLs as distinct, so the (producto_id, insumo_id,
    variante_id) unique constraint does NOT catch two rows with
    variante_id IS NULL. An explicit SELECT including `variante_id IS NULL`
    closes that hole; the IntegrityError branch is a defensive fallback.
    """
    stmt = select(BomInsumo.id).where(
        BomInsumo.producto_id == producto_id,
        BomInsumo.insumo_id == insumo_id,
    )
    if variante_id is None:
        stmt = stmt.where(BomInsumo.variante_id.is_(None))
    else:
        stmt = stmt.where(BomInsumo.variante_id == variante_id)
    if exclude_id is not None:
        stmt = stmt.where(BomInsumo.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="BomInsumo line already exists for this product, insumo and variant",
        )


def _validar_linea_producto_unica(
    db: Session, combo_id: int, producto_incluido_id: int, exclude_id: int | None = None
) -> None:
    stmt = select(BomProducto.id).where(
        BomProducto.combo_id == combo_id,
        BomProducto.producto_incluido_id == producto_incluido_id,
    )
    if exclude_id is not None:
        stmt = stmt.where(BomProducto.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise HTTPException(
            status_code=409, detail="BomProducto line already exists for this combo"
        )


# ---------------------------------------------------------------------------
# BOM_Insumos (nested under /productos/{producto_id}/bom/insumos)
# ---------------------------------------------------------------------------


@router.get("/{producto_id}/bom/insumos", response_model=list[BomInsumoRead])
def list_bom_insumos(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(audited_user),
):
    _get_producto_or_404(db, producto_id)
    stmt = (
        select(BomInsumo)
        .where(BomInsumo.producto_id == producto_id)
        .order_by(BomInsumo.id)
    )
    return list(db.scalars(stmt).all())


@router.post(
    "/{producto_id}/bom/insumos",
    response_model=BomInsumoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_bom_insumo(
    producto_id: int,
    payload: BomInsumoCreate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    _get_producto_or_404(db, producto_id)
    if db.get(Insumo, payload.insumo_id) is None:
        raise HTTPException(status_code=400, detail="Insumo does not exist")
    if payload.variante_id is not None:
        _validar_variante_del_producto(db, producto_id, payload.variante_id)
    validar_linea_insumo_unica(db, producto_id, payload.insumo_id, payload.variante_id)
    linea = BomInsumo(producto_id=producto_id, **payload.model_dump())
    db.add(linea)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="BomInsumo line already exists for this product, insumo and variant",
        )
    db.refresh(linea)
    return linea


@router.put("/{producto_id}/bom/insumos/{linea_id}", response_model=BomInsumoRead)
def update_bom_insumo(
    producto_id: int,
    linea_id: int,
    payload: BomInsumoUpdate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    _get_producto_or_404(db, producto_id)
    linea = db.get(BomInsumo, linea_id)
    if linea is None or linea.producto_id != producto_id:
        raise HTTPException(status_code=404, detail="BomInsumo not found")
    updates = payload.model_dump(exclude_unset=True)
    nuevo_insumo_id = updates.get("insumo_id", linea.insumo_id)
    nueva_variante_id = updates.get("variante_id", linea.variante_id)
    if nuevo_insumo_id != linea.insumo_id and db.get(Insumo, nuevo_insumo_id) is None:
        raise HTTPException(status_code=400, detail="Insumo does not exist")
    if nueva_variante_id is not None:
        _validar_variante_del_producto(db, producto_id, nueva_variante_id)
    validar_linea_insumo_unica(
        db, producto_id, nuevo_insumo_id, nueva_variante_id, exclude_id=linea_id
    )
    for field, value in updates.items():
        setattr(linea, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="BomInsumo line already exists for this product, insumo and variant",
        )
    db.refresh(linea)
    return linea


@router.delete(
    "/{producto_id}/bom/insumos/{linea_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_bom_insumo(
    producto_id: int,
    linea_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    _get_producto_or_404(db, producto_id)
    linea = db.get(BomInsumo, linea_id)
    if linea is None or linea.producto_id != producto_id:
        raise HTTPException(status_code=404, detail="BomInsumo not found")
    db.delete(linea)
    db.commit()


# ---------------------------------------------------------------------------
# BOM_Productos (nested under /productos/{producto_id}/bom/productos)
# ---------------------------------------------------------------------------


@router.get("/{producto_id}/bom/productos", response_model=list[BomProductoRead])
def list_bom_productos(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(audited_user),
):
    _get_producto_or_404(db, producto_id)
    stmt = (
        select(BomProducto)
        .where(BomProducto.combo_id == producto_id)
        .order_by(BomProducto.id)
    )
    return list(db.scalars(stmt).all())


@router.post(
    "/{producto_id}/bom/productos",
    response_model=BomProductoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_bom_producto(
    producto_id: int,
    payload: BomProductoCreate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    _get_producto_or_404(db, producto_id)
    if db.get(Producto, payload.producto_incluido_id) is None:
        raise HTTPException(status_code=400, detail="Producto does not exist")
    _validar_linea_producto_unica(db, producto_id, payload.producto_incluido_id)
    linea = BomProducto(combo_id=producto_id, **payload.model_dump())
    db.add(linea)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="BomProducto line already exists for this combo"
        )
    db.refresh(linea)
    return linea


@router.put("/{producto_id}/bom/productos/{linea_id}", response_model=BomProductoRead)
def update_bom_producto(
    producto_id: int,
    linea_id: int,
    payload: BomProductoUpdate,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    _get_producto_or_404(db, producto_id)
    linea = db.get(BomProducto, linea_id)
    if linea is None or linea.combo_id != producto_id:
        raise HTTPException(status_code=404, detail="BomProducto not found")
    updates = payload.model_dump(exclude_unset=True)
    nuevo_incluido_id = updates.get("producto_incluido_id", linea.producto_incluido_id)
    if nuevo_incluido_id != linea.producto_incluido_id and db.get(
        Producto, nuevo_incluido_id
    ) is None:
        raise HTTPException(status_code=400, detail="Producto does not exist")
    _validar_linea_producto_unica(
        db, producto_id, nuevo_incluido_id, exclude_id=linea_id
    )
    for field, value in updates.items():
        setattr(linea, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="BomProducto line already exists for this combo"
        )
    db.refresh(linea)
    return linea


@router.delete(
    "/{producto_id}/bom/productos/{linea_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_bom_producto(
    producto_id: int,
    linea_id: int,
    db: Session = Depends(get_db),
    _: Producto = Depends(require_admin),
):
    _get_producto_or_404(db, producto_id)
    linea = db.get(BomProducto, linea_id)
    if linea is None or linea.combo_id != producto_id:
        raise HTTPException(status_code=404, detail="BomProducto not found")
    db.delete(linea)
    db.commit()
