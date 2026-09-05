from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_roles
from app.models.audit_fiscal import PrecioVersion, CostoVersion, CierreMensual
from app.models.productos import Producto
from app.models.usuarios import Usuario

router = APIRouter(prefix="/audit-fiscal", tags=["audit-fiscal"])

audited_user = require_roles("admin", "operador", "consulta")

class PrecioVersionCreate(BaseModel):
    producto_id: int
    variante_id: int | None = None
    precio: float
    fecha_desde: date

class CostoVersionCreate(BaseModel):
    producto_id: int
    costo: float
    fecha_desde: date

class CierreCreate(BaseModel):
    periodo: str = Field(min_length=7, max_length=7, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")  # YYYY-MM

@router.get("/precio-versions")
def list_precios(producto_id: int | None = None, db: Session = Depends(get_db), _: Usuario = Depends(audited_user)):
    q = db.query(PrecioVersion)
    if producto_id: q = q.filter(PrecioVersion.producto_id == producto_id)
    return q.order_by(PrecioVersion.fecha_desde.desc()).all()

@router.post("/precio-versions", dependencies=[Depends(require_roles("admin"))])
def create_precio(payload: PrecioVersionCreate, db: Session = Depends(get_db)):
    if db.get(Producto, payload.producto_id) is None:
        raise HTTPException(status_code=400, detail="Producto no existe")
    row = PrecioVersion(**payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@router.get("/costo-versions")
def list_costos(producto_id: int | None = None, db: Session = Depends(get_db), _: Usuario = Depends(audited_user)):
    q = db.query(CostoVersion)
    if producto_id: q = q.filter(CostoVersion.producto_id == producto_id)
    return q.order_by(CostoVersion.fecha_desde.desc()).all()

@router.post("/costo-versions", dependencies=[Depends(require_roles("admin"))])
def create_costo(payload: CostoVersionCreate, db: Session = Depends(get_db)):
    if db.get(Producto, payload.producto_id) is None:
        raise HTTPException(status_code=400, detail="Producto no existe")
    row = CostoVersion(**payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@router.get("/cierres")
def list_cierres(db: Session = Depends(get_db), _: Usuario = Depends(audited_user)):
    return db.query(CierreMensual).order_by(CierreMensual.periodo.desc()).all()

@router.post("/cierres", dependencies=[Depends(require_roles("admin"))])
def create_cierre(payload: CierreCreate, db: Session = Depends(get_db)):
    if db.query(CierreMensual).filter_by(periodo=payload.periodo).first():
        raise HTTPException(409, "Periodo ya cerrado")
    row = CierreMensual(periodo=payload.periodo)
    db.add(row); db.commit(); db.refresh(row)
    return row

def is_periodo_cerrado(db: Session, periodo: str) -> bool:
    return db.query(CierreMensual).filter_by(periodo=periodo).first() is not None
