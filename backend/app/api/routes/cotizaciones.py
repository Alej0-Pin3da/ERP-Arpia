"""Cotizaciones API routes.

Persists quick quotes from the Cotizador so the priced number survives
beyond WhatsApp: every stored quote snapshots the pricing inputs and the
server-computed results (single source of truth, same math as the
frontend), and can later feed the product's ``precio_venta_sugerido``:
- POST /cotizaciones: snapshot inputs, compute results, store one atomic row.
- GET /cotizaciones: paginated {items, total} with AND-combined filters
  (cliente_id, producto_id, estado, q on nombre_prenda).
- GET /cotizaciones/{id}: one quote; 404 when missing.
- PATCH /cotizaciones/{id}/estado: move along
  borrador → enviada → aprobada/descartada.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.clientes import Cliente
from app.models.cotizacion import Cotizacion
from app.models.productos import Producto
from app.models.usuarios import Usuario
from app.schemas.common import Paginated
from app.schemas.cotizacion import CotizacionCreate, CotizacionEstadoUpdate, CotizacionRead
from app.services.paginacion import paginar

router = APIRouter(prefix="/cotizaciones", tags=["cotizaciones"])

audited_user = require_roles("admin", "operador", "consulta")
editor_user = require_roles("admin", "operador")


def _calcular(payload: CotizacionCreate) -> tuple[Decimal, Decimal, Decimal]:
    """Mirror of the Cotizador frontend math (server is authoritative)."""
    subtotal_telas = (
        payload.metros_tela * payload.precio_metro_tela
        + payload.metros_forro * payload.precio_metro_forro
    )
    subtotal_avios = payload.costo_avios + payload.costo_empaque
    subtotal_mano_obra = (
        Decimal(payload.tiempo_confeccion_min) / Decimal(60)
    ) * payload.tarifa_hora
    costo = subtotal_telas + subtotal_avios + subtotal_mano_obra + payload.costo_cif
    if payload.margen_pct >= Decimal(100):
        precio = costo * Decimal("2.2")
    else:
        factor = Decimal(1) - payload.margen_pct / Decimal(100)
        precio = costo * Decimal(2) if factor <= Decimal("0.05") else costo / factor
    return costo, precio, precio - costo


@router.post("", response_model=CotizacionRead, status_code=status.HTTP_201_CREATED)
def create_cotizacion(
    payload: CotizacionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Snapshot a quote with server-computed results (one atomic commit)."""
    if payload.cliente_id is not None and db.get(Cliente, payload.cliente_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cliente_id no existe",
        )
    if payload.producto_id is not None and db.get(Producto, payload.producto_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="producto_id no existe",
        )
    costo, precio, ganancia = _calcular(payload)
    row = Cotizacion(
        cliente_id=payload.cliente_id,
        producto_id=payload.producto_id,
        nombre_prenda=payload.nombre_prenda,
        metros_tela=payload.metros_tela,
        precio_metro_tela=payload.precio_metro_tela,
        metros_forro=payload.metros_forro,
        precio_metro_forro=payload.precio_metro_forro,
        costo_avios=payload.costo_avios,
        costo_empaque=payload.costo_empaque,
        tiempo_confeccion_min=payload.tiempo_confeccion_min,
        tarifa_hora=payload.tarifa_hora,
        costo_cif=payload.costo_cif,
        margen_pct=payload.margen_pct,
        costo_total=costo,
        precio_sugerido=precio,
        ganancia_neta=ganancia,
        observaciones=payload.observaciones,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=Paginated[CotizacionRead])
def list_cotizaciones(
    limit: int = 50,
    offset: int = 0,
    cliente_id: int | None = None,
    producto_id: int | None = None,
    estado: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Paginated quotes with AND-combined filters."""
    stmt = select(Cotizacion)
    if cliente_id is not None:
        stmt = stmt.where(Cotizacion.cliente_id == cliente_id)
    if producto_id is not None:
        stmt = stmt.where(Cotizacion.producto_id == producto_id)
    if estado is not None:
        stmt = stmt.where(Cotizacion.estado == estado)
    if q is not None:
        stmt = stmt.where(Cotizacion.nombre_prenda.ilike(f"%{q}%"))
    stmt = stmt.order_by(Cotizacion.id.desc())
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[CotizacionRead](items=list(rows), total=total)


@router.get("/{cotizacion_id}", response_model=CotizacionRead)
def get_cotizacion(
    cotizacion_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """One quote; 404 when missing."""
    row = db.get(Cotizacion, cotizacion_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada",
        )
    return row


@router.patch("/{cotizacion_id}/estado", response_model=CotizacionRead)
def update_cotizacion_estado(
    cotizacion_id: int,
    payload: CotizacionEstadoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Move a quote along its state machine; 404 when missing."""
    row = db.get(Cotizacion, cotizacion_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada",
        )
    row.estado = payload.estado
    db.commit()
    db.refresh(row)
    return row
