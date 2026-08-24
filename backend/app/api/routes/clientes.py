from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.clientes import Cliente
from app.schemas.cliente import ClienteCreate, ClienteRead, ClienteUpdate
from app.schemas.common import Paginated
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/clientes", tags=["clientes"])

audited_user = require_roles("admin", "operador", "consulta")

# Whitelisted server-side sort keys (plain columns on Cliente).
_SORTABLE_CLIENTES = {
    "id": Cliente.id,
    "nombre": Cliente.nombre,
}


@router.get("", response_model=Paginated[ClienteRead])
def list_clientes(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    tipo: str | None = None,
    ciudad: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Cliente = Depends(audited_user),
):
    stmt = select(Cliente).order_by(Cliente.id)
    if tipo is not None:
        stmt = stmt.where(Cliente.tipo == tipo)
    if ciudad is not None:
        stmt = stmt.where(Cliente.ciudad == ciudad)
    if q is not None:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Cliente.nombre.ilike(like),
                Cliente.ciudad.ilike(like),
                Cliente.direccion.ilike(like),
            )
        )
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_CLIENTES)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[ClienteRead](items=list(rows), total=total)


@router.get("/{cliente_id}", response_model=ClienteRead)
def get_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Cliente = Depends(audited_user),
):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return cliente


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def create_cliente(
    payload: ClienteCreate,
    db: Session = Depends(get_db),
    _: Cliente = Depends(require_admin),
):
    cliente = Cliente(**payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.put("/{cliente_id}", response_model=ClienteRead)
def update_cliente(
    cliente_id: int,
    payload: ClienteUpdate,
    db: Session = Depends(get_db),
    _: Cliente = Depends(require_admin),
):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, field, value)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Cliente = Depends(require_admin),
):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente not found")
    db.delete(cliente)
    db.commit()
