from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_admin, require_roles
from app.core.exceptions import DomainError
from app.models.produccion import (
    PedidoProduccion,
    PedidoProduccionEstado,
    PedidoProduccionPrioridad,
    PrendaConfeccionada,
    PrendaEstado,
    TiempoFase,
)
from app.models.productos import Producto, VarianteProducto
from app.models.clientes import Cliente
from app.schemas.common import Paginated
from app.schemas.produccion import (
    PedidoProduccionCreate,
    PedidoProduccionRead,
    PedidoProduccionUpdate,
    PrendaConfeccionadaCreate,
    PrendaConfeccionadaRead,
    PrendaConfeccionadaUpdate,
    TiempoFaseCreate,
    TiempoFaseRead,
    TiempoFaseUpdate,
    TiemposListRead,
)
from app.services.paginacion import aplicar_orden, paginar
from app.services.costos import tasas_costeo
from app.services.produccion import (
    completar_lote,
    pedido_esta_completado,
    totales_tiempos,
    validar_avance_fase,
    validar_fase_tiempo,
)

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
    "fase": PedidoProduccion.fase,
    "prioridad": PedidoProduccion.prioridad,
    "fecha_pedido": PedidoProduccion.fecha_pedido,
    "fecha_entrega_estimada": PedidoProduccion.fecha_entrega_estimada,
    "created_at": PedidoProduccion.created_at,
}


def _pedido_to_read(
    pedido: PedidoProduccion, db: Session | None = None
) -> PedidoProduccionRead:
    res = PedidoProduccionRead.model_validate(pedido)
    if pedido.producto is not None:
        res.nombre_producto = pedido.producto.nombre
    if pedido.variante is not None:
        res.nombre_variante = pedido.variante.nombre_variante
    if pedido.cliente is not None:
        res.cliente_nombre = pedido.cliente.nombre
    # Read-time real cost (None while no tiempos exist — "no data", not 0).
    if db is not None and pedido.id is not None:
        totales = totales_tiempos(db, pedido.id)
        tiene = db.scalar(
            select(TiempoFase.id).where(TiempoFase.pedido_id == pedido.id)
        )
        if tiene is not None:
            res.mano_obra_real = totales["mano_obra_real"]
            res.energia_real = totales["energia_real"]
    return res


@router_pedidos.get("", response_model=Paginated[PedidoProduccionRead])
def list_pedidos(
    limit: int = 50,
    offset: int = 0,
    producto_id: int | None = None,
    variante_id: int | None = None,
    estado: str | None = None,
    fase: str | None = None,
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
            selectinload(PedidoProduccion.cliente),
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
    if fase is not None:
        stmt = stmt.where(PedidoProduccion.fase == fase)
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
        items=[_pedido_to_read(p, db) for p in rows], total=total
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
    return _pedido_to_read(pedido, db)


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
    if payload.cliente_id is not None and db.get(Cliente, payload.cliente_id) is None:
        raise HTTPException(status_code=400, detail="Cliente no existe")

    pedido = PedidoProduccion(**payload.model_dump())
    db.add(pedido)
    try:
        db.flush()
        # Creating straight into listo/completado completes the lot at once.
        if pedido_esta_completado(pedido):
            completar_lote(db, pedido)
        db.commit()
        db.refresh(pedido)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e
    except DomainError:
        # 409 shortage (per-insumo detail) / 404 / 422: nothing is persisted.
        db.rollback()
        raise

    return _pedido_to_read(pedido, db)


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
    if payload.cliente_id is not None and db.get(Cliente, payload.cliente_id) is None:
        raise HTTPException(status_code=400, detail="Cliente no existe")

    data = payload.model_dump(exclude_unset=True)
    # Phase moves validated BEFORE mutating (422 unknown fase, 400 skip
    # forward / out of listo; backward to any earlier phase is devolución),
    # so a rejected PATCH leaves the session untouched.
    if "fase" in data and data["fase"] is not None and data["fase"] != pedido.fase:
        validar_avance_fase(pedido.fase, data["fase"])

    estaba_completado = pedido_esta_completado(pedido)
    for k, v in data.items():
        setattr(pedido, k, v)

    try:
        db.flush()
        # Idempotent completion: runs ONCE when transitioning INTO listo or
        # completado. 409 shortage carries per-insumo detail, no partial commit.
        if pedido_esta_completado(pedido) and not estaba_completado:
            completar_lote(db, pedido)
        db.commit()
        db.refresh(pedido)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e
    except DomainError:
        db.rollback()
        raise

    return _pedido_to_read(pedido, db)


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


# --- Tiempos por fase (nested) ---
# One row per (pedido, fase): POST creates, PATCH corrects minutes/operaria.
# Money is derived at read time (mano: minutos x global rate, all phases;
# energia: minutos x global rate, 'costura' only, 0 otherwise), never stored.


def _tiempo_to_read(
    tiempo: TiempoFase, tasa_mano: Decimal, tasa_energia: Decimal
) -> TiempoFaseRead:
    res = TiempoFaseRead.model_validate(tiempo)
    res.costo_mano_obra = tiempo.minutos_reales * tasa_mano
    # ENERGY only in 'costura' (sewing machines); corte/acabados/calidad
    # are manual — zero energy. Labor counts every phase.
    res.costo_energia = (
        tiempo.minutos_reales * tasa_energia
        if tiempo.fase == "costura"
        else Decimal("0")
    )
    return res


def _get_pedido_or_404(db: Session, pedido_id: int) -> PedidoProduccion:
    pedido = db.get(PedidoProduccion, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido de producción no encontrado")
    return pedido


@router_pedidos.get("/{pedido_id}/tiempos", response_model=TiemposListRead)
def list_tiempos(
    pedido_id: int,
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(audited_user),
):
    _get_pedido_or_404(db, pedido_id)
    rows = db.scalars(
        select(TiempoFase)
        .where(TiempoFase.pedido_id == pedido_id)
        .order_by(TiempoFase.id.asc())
    ).all()
    tasa_mano, tasa_energia = tasas_costeo(db)
    items = [_tiempo_to_read(t, tasa_mano, tasa_energia) for t in rows]
    return TiemposListRead(
        items=items,
        total_minutos=sum((t.minutos_reales for t in rows), Decimal("0")),
        total_mano_obra=sum(
            (t.costo_mano_obra for t in items if t.costo_mano_obra is not None),
            Decimal("0"),
        ),
        total_energia=sum(
            (t.costo_energia for t in items if t.costo_energia is not None),
            Decimal("0"),
        ),
    )


@router_pedidos.post(
    "/{pedido_id}/tiempos", response_model=TiempoFaseRead, status_code=status.HTTP_201_CREATED
)
def create_tiempo(
    pedido_id: int,
    payload: TiempoFaseCreate,
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(require_admin),
):
    pedido = _get_pedido_or_404(db, pedido_id)
    # Sequential-order guard BEFORE mutating (422 unknown/listo, 400 ahead).
    validar_fase_tiempo(pedido.fase, payload.fase)
    operaria = payload.operaria.strip()
    if not operaria:
        raise HTTPException(status_code=400, detail="Operaria no puede estar vacía")
    existente = db.scalar(
        select(TiempoFase.id).where(
            TiempoFase.pedido_id == pedido_id, TiempoFase.fase == payload.fase
        )
    )
    if existente is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Ya existe un registro de tiempo para la fase '{payload.fase}' "
                f"en el pedido {pedido_id} (use PATCH para corregir)"
            ),
        )
    tiempo = TiempoFase(
        pedido_id=pedido_id,
        fase=payload.fase,
        operaria=operaria,
        minutos_reales=payload.minutos_reales,
        fecha=payload.fecha or date.today(),
    )
    db.add(tiempo)
    try:
        db.commit()
        db.refresh(tiempo)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e
    tasa_mano, tasa_energia = tasas_costeo(db)
    return _tiempo_to_read(tiempo, tasa_mano, tasa_energia)


@router_pedidos.patch("/{pedido_id}/tiempos/{tiempo_id}", response_model=TiempoFaseRead)
def update_tiempo(
    pedido_id: int,
    tiempo_id: int,
    payload: TiempoFaseUpdate,
    db: Session = Depends(get_db),
    _: PedidoProduccion = Depends(require_admin),
):
    _get_pedido_or_404(db, pedido_id)
    tiempo = db.get(TiempoFase, tiempo_id)
    if tiempo is None or tiempo.pedido_id != pedido_id:
        raise HTTPException(status_code=404, detail="Registro de tiempo no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "operaria" in data and data["operaria"] is not None:
        operaria = data["operaria"].strip()
        if not operaria:
            raise HTTPException(status_code=400, detail="Operaria no puede estar vacía")
        tiempo.operaria = operaria
    if "minutos_reales" in data and data["minutos_reales"] is not None:
        tiempo.minutos_reales = data["minutos_reales"]
    try:
        db.commit()
        db.refresh(tiempo)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Error de integridad: {e}") from e
    tasa_mano, tasa_energia = tasas_costeo(db)
    return _tiempo_to_read(tiempo, tasa_mano, tasa_energia)
