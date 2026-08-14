from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.proveedores import Proveedor
from app.schemas.common import Paginated
from app.schemas.proveedor import ProveedorCreate, ProveedorRead, ProveedorUpdate
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/proveedores", tags=["proveedores"])

audited_user = require_roles("admin", "operador", "consulta")

# Whitelisted server-side sort keys (all plain columns on Proveedor).
_SORTABLE_PROVEEDORES = {
    "id": Proveedor.id,
    "nombre": Proveedor.nombre,
    "ubicacion": Proveedor.ubicacion,
    "contacto": Proveedor.contacto,
}


@router.get("", response_model=Paginated[ProveedorRead])
def list_proveedores(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Proveedor = Depends(audited_user),
):
    stmt = select(Proveedor).order_by(Proveedor.id)
    if q is not None:
        stmt = stmt.where(
            or_(
                Proveedor.nombre.ilike(f"%{q}%"),
                Proveedor.ubicacion.ilike(f"%{q}%"),
                Proveedor.contacto.ilike(f"%{q}%"),
            )
        )
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_PROVEEDORES)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[ProveedorRead](items=list(rows), total=total)


@router.get("/{proveedor_id}", response_model=ProveedorRead)
def get_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    _: Proveedor = Depends(audited_user),
):
    proveedor = db.get(Proveedor, proveedor_id)
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    return proveedor


@router.post("", response_model=ProveedorRead, status_code=status.HTTP_201_CREATED)
def create_proveedor(
    payload: ProveedorCreate,
    db: Session = Depends(get_db),
    _: Proveedor = Depends(require_admin),
):
    proveedor = Proveedor(**payload.model_dump())
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.put("/{proveedor_id}", response_model=ProveedorRead)
def update_proveedor(
    proveedor_id: int,
    payload: ProveedorUpdate,
    db: Session = Depends(get_db),
    _: Proveedor = Depends(require_admin),
):
    proveedor = db.get(Proveedor, proveedor_id)
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(proveedor, field, value)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.delete("/{proveedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    _: Proveedor = Depends(require_admin),
):
    proveedor = db.get(Proveedor, proveedor_id)
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    db.delete(proveedor)
    db.commit()
