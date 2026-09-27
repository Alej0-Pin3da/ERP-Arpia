"""Kits API routes (V6 M1).

Promotional boxes over live product costs: every read carries a fresh cost
snapshot (``costo_total``/``margen_pct``/``alerta_margen``); the margin
alert is visual, never a block. Mutations are single-commit atomic.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.kits import Kit, KitProducto
from app.models.usuarios import Usuario
from app.schemas.common import Paginated
from app.schemas.kit import KitCreate, KitLineaCreate, KitRead, KitUpdate
from app.services import kits as kits_service
from app.services.paginacion import paginar

router = APIRouter(prefix="/kits", tags=["kits"])

audited_user = require_roles("admin", "operador", "consulta")
editor_user = require_roles("admin", "operador")


def _a_read(db: Session, kit: Kit) -> dict:
    snap = kits_service.costear_kit(db, kit)
    return {
        "id": kit.id,
        "nombre": kit.nombre,
        "precio_promocional": kit.precio_promocional,
        "activo": kit.activo,
        **snap,
    }


@router.post("", response_model=KitRead, status_code=status.HTTP_201_CREATED)
def create_kit(
    payload: KitCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Create a kit with its product lines (one atomic commit)."""
    kit = kits_service.crear_kit(db, payload.nombre, payload.precio_promocional)
    try:
        for linea in payload.lineas:
            kits_service.agregar_linea(db, kit, linea.producto_id, linea.cantidad)
    except HTTPException:
        db.delete(kit)
        db.commit()
        raise
    db.refresh(kit)
    return _a_read(db, kit)


@router.get("", response_model=Paginated[KitRead])
def list_kits(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Paginated kits (each with its live cost snapshot)."""
    stmt = select(Kit)
    if q is not None:
        stmt = stmt.where(Kit.nombre.ilike(f"%{q}%"))
    stmt = stmt.order_by(Kit.id.desc())
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[KitRead](
        items=[_a_read(db, kit) for kit in rows], total=total  # type: ignore[arg-type]
    )


@router.get("/{kit_id}", response_model=KitRead)
def get_kit(
    kit_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """One kit with its live cost snapshot; 404 when missing."""
    return _a_read(db, kits_service.obtener_kit(db, kit_id))


@router.patch("/{kit_id}", response_model=KitRead)
def update_kit(
    kit_id: int,
    payload: KitUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Update nombre/precio/activo; 404 when missing."""
    kit = kits_service.obtener_kit(db, kit_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(kit, field, value)
    db.commit()
    db.refresh(kit)
    return _a_read(db, kit)


@router.delete("/{kit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kit(
    kit_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Delete a kit and its lines (CASCADE); 404 when missing."""
    db.delete(kits_service.obtener_kit(db, kit_id))
    db.commit()
    return None


@router.post("/{kit_id}/lineas", response_model=KitRead, status_code=status.HTTP_201_CREATED)
def add_linea(
    kit_id: int,
    payload: KitLineaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Add a product line (409 on duplicate, 422 on unknown product)."""
    kit = kits_service.obtener_kit(db, kit_id)
    kits_service.agregar_linea(db, kit, payload.producto_id, payload.cantidad)
    db.refresh(kit)
    return _a_read(db, kit)


@router.delete("/{kit_id}/lineas/{linea_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_linea(
    kit_id: int,
    linea_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Remove a product line; 404 when missing or foreign to the kit."""
    linea = db.get(KitProducto, linea_id)
    if linea is None or linea.kit_id != kit_id:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    db.delete(linea)
    db.commit()
    return None
