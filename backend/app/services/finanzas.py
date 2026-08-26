"""Finanzas engine — financial movements, partner-config and settlements.

Owns the business rules the DB cannot express: the multi-row invariant
"sum of partner participation == 100" is validated here at the service layer
(create requires an exact 100 total; updates may rebalance *below* 100 while
another partner completes validation, but never above), and settlements are
one-time per ``liquidacion_id`` (the partial unique index is the last line of
defense; the service rejects replays with 409 before writing).
"""

import secrets
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.finanzas import (
    Anticipo,
    AnticipoEstado,
    DistribucionEstado,
    Liquidacion,
    LiquidacionDistribucion,
    LiquidacionEstado,
    MovimientoFinanciero,
    SociosConfiguracion,
)
from app.models.ventas import DocumentState


def _suma_participacion(db: Session) -> Decimal:
    total = Decimal("0")
    for socio in db.scalars(select(SociosConfiguracion)):
        total += socio.porcentaje_participacion
    return total


# ---------------------------------------------------------------------------
# FIN-1: MovimientoFinanciero CRUD
# ---------------------------------------------------------------------------


def crear_movimiento(db: Session, payload: dict) -> MovimientoFinanciero:
    """Create a financial movement (tipo Gasto|Inversion|Retiro)."""
    socio_id = payload.get("socio_id")
    if socio_id is not None:
        if db.get(SociosConfiguracion, socio_id) is None:
            raise HTTPException(status_code=400, detail="Socio no existe")

    movimiento = MovimientoFinanciero(
        tipo=payload["tipo"],
        descripcion=payload["descripcion"],
        monto=Decimal(payload["monto"]),
        socio_id=socio_id,
    )
    db.add(movimiento)
    try:
        db.commit()
        db.refresh(movimiento)
        return movimiento
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto al crear el movimiento; no se persistió nada",
        ) from None
    except Exception:
        db.rollback()
        raise


def listar_movimientos(
    db: Session, estado: str = DocumentState.CONFIRMED.value
) -> list[MovimientoFinanciero]:
    """List movements ordered by id, filtered by estado (soft-delete aware)."""
    stmt = (
        select(MovimientoFinanciero)
        .where(MovimientoFinanciero.estado == estado)
        .order_by(MovimientoFinanciero.id)
    )
    return list(db.scalars(stmt))


def eliminar_movimiento(db: Session, movimiento_id: int) -> MovimientoFinanciero:
    """Soft delete a movement (estado -> 'cancelled')."""
    movimiento = db.get(MovimientoFinanciero, movimiento_id)
    if movimiento is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    try:
        movimiento.transition_to(DocumentState.CANCELLED)
        db.commit()
        db.refresh(movimiento)
        return movimiento
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from None


def actualizar_movimiento(db: Session, movimiento_id: int, payload: dict) -> MovimientoFinanciero:
    """Partial update of a movement (FIN-1 PATCH).

    Applies ONLY the fields present in ``payload`` (the route passes
    ``model_dump(exclude_unset=True)``). Rules, in order:
    - missing id or soft-deleted (estado != 'activo') -> 404;
    - FIN-2 server-side guard: a liquidacion-born row freezes monto/socio_id —
      any attempt to send either field -> 422 (fecha/tipo/descripcion remain
      editable);
    - a concrete socio_id that does not exist -> 400 "Socio no existe"
      (consistent with crear_movimiento).
    """
    movimiento = db.get(MovimientoFinanciero, movimiento_id)
    if movimiento is None or movimiento.estado != DocumentState.CONFIRMED.value:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")

    # FIN-2: the server is the backstop — UI disabling is not enough.
    if movimiento.liquidacion_id is not None and {"monto", "socio_id"} & payload.keys():
        raise HTTPException(
            status_code=422,
            detail="Los movimientos de una liquidación no permiten cambiar monto ni socio",
        )

    if "socio_id" in payload and payload["socio_id"] is not None:
        if db.get(SociosConfiguracion, payload["socio_id"]) is None:
            raise HTTPException(status_code=400, detail="Socio no existe")

    for campo, valor in payload.items():
        setattr(movimiento, campo, valor)
    db.commit()
    db.refresh(movimiento)
    return movimiento


def settle_liquidacion(
    db: Session,
    monto: str | Decimal,
    notas: str | None = None,
    liquidacion_id: str | None = None,
) -> list[MovimientoFinanciero]:
    """One-time proportional settlement across all socios.

    Creates one 'Retiro' per socio for ``monto * porcentaje / 100`` and commits
    atomically. The settlement key (caller-provided ``liquidacion_id`` truncated
    to 10 chars, or a fresh 10-char token) becomes each row's
    ``liquidacion_id`` as ``<key><2-digit index>`` — the partial unique index
    ``uq_liquidacion`` (one non-null value per row) forbids two rows sharing a
    raw id, so per-socio rows carry distinct ids derived from ONE settlement
    key. A replay (any existing row whose id starts with the same key) raises
    409 before writing; the unique index remains the hard backstop against
    concurrent replays.
    """
    if liquidacion_id is None:
        key = secrets.token_hex(5)  # 10 chars; rows get key + 2-digit index
    else:
        key = liquidacion_id[:10]
        existente = db.scalar(
            select(MovimientoFinanciero).where(MovimientoFinanciero.liquidacion_id.like(f"{key}%"))
        )
        if existente is not None:
            raise HTTPException(
                status_code=409,
                detail=f"La liquidación {key} ya fue procesada",
            )

    monto_dec = Decimal(monto)
    movimientos: list[MovimientoFinanciero] = []
    for i, socio in enumerate(
        db.scalars(select(SociosConfiguracion).order_by(SociosConfiguracion.id))
    ):
        movimientos.append(
            MovimientoFinanciero(
                tipo="Retiro",
                descripcion=notas or f"Liquidación {key}",
                monto=monto_dec * socio.porcentaje_participacion / Decimal("100"),
                socio_id=socio.id,
                liquidacion_id=f"{key}{i:02d}",
            )
        )
    db.add_all(movimientos)
    try:
        db.commit()
        for mov in movimientos:
            db.refresh(mov)
        return movimientos
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto al liquidar; la liquidación ya fue procesada",
        ) from None
    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------------------------
# FIN-2: SociosConfiguracion — sum-to-100 invariant (service layer)
# ---------------------------------------------------------------------------


def crear_socio_configuracion(db: Session, nombre: str, porcentaje: Decimal) -> SociosConfiguracion:
    """Create a partner row; the GLOBAL sum must land exactly on 100 (else 422)."""
    porcentaje = Decimal(porcentaje)
    if _suma_participacion(db) + porcentaje != Decimal("100"):
        raise HTTPException(
            status_code=422,
            detail="La suma de porcentajes de participación debe ser exactamente 100",
        )
    socio = SociosConfiguracion(nombre=nombre, porcentaje_participacion=porcentaje)
    db.add(socio)
    try:
        db.commit()
        db.refresh(socio)
        return socio
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un socio con ese nombre",
        ) from None
    except Exception:
        db.rollback()
        raise


def actualizar_socio_configuracion(
    db: Session, socio_id: int, porcentaje: Decimal
) -> SociosConfiguracion:
    """Update a partner's share.

    The resulting global sum may drop below 100 (interim rebalancing while
    another partner completes validation) but must NEVER exceed 100 (422).
    """
    socio = db.get(SociosConfiguracion, socio_id)
    if socio is None:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    porcentaje = Decimal(porcentaje)
    resto = _suma_participacion(db) - socio.porcentaje_participacion
    if resto + porcentaje > Decimal("100"):
        raise HTTPException(
            status_code=422,
            detail="La suma de porcentajes de participación no puede superar 100",
        )
    socio.porcentaje_participacion = porcentaje
    db.commit()
    db.refresh(socio)
    return socio


def eliminar_socio_configuracion(db: Session, socio_id: int) -> None:
    """Delete a partner row; blocked with 409 when the socio already has
    payouts (any MovimientoFinanciero referencing it)."""
    socio = db.get(SociosConfiguracion, socio_id)
    if socio is None:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    con_pagos = db.scalar(
        select(MovimientoFinanciero).where(MovimientoFinanciero.socio_id == socio_id)
    )
    if con_pagos is not None:
        raise HTTPException(
            status_code=409,
            detail="El socio tiene movimientos asociados; no se puede eliminar",
        )
    db.delete(socio)
    db.commit()


# ---------------------------------------------------------------------------
# v4 — SOC-2: extended socia profile, sum-to-100 over activo=true incl fondo
# ---------------------------------------------------------------------------


def _suma_participacion_activa(db: Session) -> Decimal:
    """Sum of ``porcentaje_participacion`` over rows where activo=true."""
    total = Decimal("0")
    for socio in db.scalars(select(SociosConfiguracion).where(SociosConfiguracion.activo.is_(True))):
        total += socio.porcentaje_participacion
    return total


def _hay_fondo_activo(db: Session, excepto_id: int | None = None) -> bool:
    stmt = select(SociosConfiguracion).where(
        SociosConfiguracion.es_fondo_taller.is_(True),
        SociosConfiguracion.activo.is_(True),
    )
    if excepto_id is not None:
        stmt = stmt.where(SociosConfiguracion.id != excepto_id)
    return db.scalar(stmt) is not None


def crear_socia_configuracion(db: Session, *, nombre: str, porcentaje, **extras) -> SociosConfiguracion:
    """Create a socia with the extended profile (SOC-1/SOC-2).

    Invariants (service layer — Postgres cannot enforce a cross-row sum):
    - the new row counts toward the sum only when ``activo=True``;
    - the resulting active sum must NOT exceed 100 (422) — building up to 100
      row by row is allowed (interim), matching the v4 40+30+30 model;
    - at most ONE active ``es_fondo_taller`` row is allowed (422 on a second).
    """
    porcentaje = Decimal(porcentaje)
    activo = extras.get("activo", True)
    es_fondo = extras.get("es_fondo_taller", False)
    if es_fondo and _hay_fondo_activo(db):
        raise HTTPException(
            status_code=422,
            detail="Solo se permite un fondo activo de reinversión",
        )
    if activo and _suma_participacion_activa(db) + porcentaje > Decimal("100"):
        raise HTTPException(
            status_code=422,
            detail="La suma de porcentajes de participación activa no puede superar 100",
        )
    socio = SociosConfiguracion(nombre=nombre, porcentaje_participacion=porcentaje, **extras)
    db.add(socio)
    try:
        db.commit()
        db.refresh(socio)
        return socio
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un socio con ese nombre",
        ) from None
    except Exception:
        db.rollback()
        raise


def actualizar_socia_configuracion(
    db: Session, socio_id: int, cambios: dict
) -> SociosConfiguracion:
    """Partial update of a socia profile (SOC-1 PATCH) enforcing SOC-2.

    Only the fields in ``cambios`` are applied. Recomputes the active sum with
    the new ``porcentaje_participacion`` and new ``activo`` state; rejects if the
    resulting active sum exceeds 100 (422), and rejects a second active fondo.
    """
    socio = db.get(SociosConfiguracion, socio_id)
    if socio is None:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    if cambios.get("es_fondo_taller") is True and _hay_fondo_activo(db, excepto_id=socio_id):
        raise HTTPException(
            status_code=422,
            detail="Solo se permite un fondo activo de reinversión",
        )

    nuevo_porcentaje = Decimal(cambios.get("porcentaje_participacion", socio.porcentaje_participacion))
    nuevo_activo = cambios.get("activo", socio.activo)
    # contribución de esta socia a la suma: su porcentaje solo si queda activa
    contribucion = nuevo_porcentaje if nuevo_activo else Decimal("0")
    suma_resto = _suma_participacion_activa(db)
    if socio.activo:
        suma_resto -= socio.porcentaje_participacion
    if suma_resto + contribucion > Decimal("100"):
        resultado = suma_resto + contribucion
        raise HTTPException(
            status_code=422,
            detail=f"La suma de porcentajes activa quedaría en {resultado} (>100)",
        )

    for campo, valor in cambios.items():
        setattr(socio, campo, valor)
    db.commit()
    db.refresh(socio)
    return socio


def listar_socias(
    db: Session,
    *,
    activo: bool | None = None,
    es_fondo_taller: bool | None = None,
    rol: str | None = None,
    q: str | None = None,
) -> list[SociosConfiguracion]:
    """Composable filtering for GET /finanzas/socios (SOC-3)."""
    stmt = select(SociosConfiguracion).order_by(SociosConfiguracion.id)
    if activo is not None:
        stmt = stmt.where(SociosConfiguracion.activo.is_(activo))
    if es_fondo_taller is not None:
        stmt = stmt.where(SociosConfiguracion.es_fondo_taller.is_(es_fondo_taller))
    if rol is not None:
        stmt = stmt.where(SociosConfiguracion.rol == rol)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            SociosConfiguracion.nombre.ilike(like)
            | SociosConfiguracion.email.ilike(like)
            | SociosConfiguracion.telefono.ilike(like)
        )
    return list(db.scalars(stmt))


# ---------------------------------------------------------------------------
# v4 — LIQ-1/2/3: real liquidaciones (header + distribution)
# ---------------------------------------------------------------------------


def _siguiente_codigo_liquidacion(db: Session, anio: int) -> str:
    """Sequential per-year codigo LIQ-YYYY-NN (LIQ-1)."""
    prefijo = f"LIQ-{anio}-"
    ultimo = db.scalar(
        select(func.max(Liquidacion.codigo)).where(Liquidacion.codigo.like(f"{prefijo}%"))
    )
    if ultimo is None:
        siguiente = 1
    else:
        siguiente = int(ultimo.rsplit("-", 1)[1]) + 1
    return f"{prefijo}{siguiente:02d}"


def _suma_movimientos_periodo(db: Session) -> Decimal:
    """Audit benchmark: sum of confirmed Movimientos_Financieros (LIQ-3)."""
    total = db.scalar(
        select(func.coalesce(func.sum(MovimientoFinanciero.monto), Decimal("0"))).where(
            MovimientoFinanciero.estado == DocumentState.CONFIRMED.value
        )
    )
    return Decimal(total or 0)


def crear_liquidacion(db: Session, payload: dict) -> tuple[Liquidacion, list[str]]:
    """Create a real liquidacion header + distribution rows atomically (LIQ-1).

    - validates ``utilidad_neta_total == total_ventas_brutas - costo_taller_insumos
      - gastos_operativos`` (else 422);
    - audits payload vs the sum of confirmed Movimientos_Financieros: >5% drift
      persists with a warning (LIQ-3);
    - computes distribution over ALL activo=true socias incl the fondo; each row
      ``monto_bruto = utilidad_repartible * porcentaje/100``, ``deduccion`` = sum of
      PENDIENTE_DESCUENTO anticipos, ``neto = bruto - deduccion`` (LIQ-3);
    - marks those anticipos DESCONTADO and links them to the new liquidacion in
      the same transaction (ANT-2);
    - ``codigo`` is LIQ-YYYY-NN sequential; IntegrityError on a concurrent
      collision -> 409 (ANT-3).
    """
    tvb = Decimal(payload["total_ventas_brutas"])
    costo = Decimal(payload["costo_taller_insumos"])
    gastos = Decimal(payload["gastos_operativos"])
    neta = Decimal(payload["utilidad_neta_total"])
    if neta != tvb - costo - gastos:
        raise HTTPException(
            status_code=422,
            detail="utilidad_neta_total debe ser total_ventas_brutas - costo - gastos",
        )

    warnings: list[str] = []
    benchmark = _suma_movimientos_periodo(db)
    if benchmark > 0:
        drift = abs(neta - benchmark) / benchmark
        if drift > Decimal("0.05"):
            warnings.append("drift >5% vs movimientos")

    socias = db.scalars(
        select(SociosConfiguracion).where(SociosConfiguracion.activo.is_(True)).order_by(SociosConfiguracion.id)
    ).all()
    if not socias:
        raise HTTPException(status_code=422, detail="No hay socias activas para liquidar")

    repartible = Decimal(payload["utilidad_repartible"])
    fondo_reinversion = Decimal(payload.get("fondo_reinversion_monto", "0"))
    if any(s.es_fondo_taller for s in socias):
        fondo_reinversion = (neta * Decimal("40") / Decimal("100")).quantize(Decimal("0.01"))

    anio = payload["fecha_cierre"].year if hasattr(payload["fecha_cierre"], "year") else date.today().year
    codigo = _siguiente_codigo_liquidacion(db, anio)

    liq = Liquidacion(
        codigo=codigo,
        periodo=payload["periodo"],
        fecha_cierre=payload["fecha_cierre"],
        total_ventas_brutas=tvb,
        costo_taller_insumos=costo,
        gastos_operativos=gastos,
        utilidad_neta_total=neta,
        fondo_reinversion_monto=fondo_reinversion,
        utilidad_repartible=repartible,
        estado=LiquidacionEstado.BORRADOR.value,
        observaciones=payload.get("observaciones"),
    )
    db.add(liq)
    db.flush()

    rows: list[LiquidacionDistribucion] = []
    anticipos_a_descontar: list[Anticipo] = []
    for socia in socias:
        bruto = (repartible * socia.porcentaje_participacion / Decimal("100")).quantize(Decimal("0.01"))
        pendientes = db.scalars(
            select(Anticipo)
            .where(
                Anticipo.socia_id == socia.id,
                Anticipo.estado == AnticipoEstado.PENDIENTE_DESCUENTO.value,
            )
            .with_for_update()
        ).all()
        deduccion = sum((a.monto for a in pendientes), Decimal("0")).quantize(Decimal("0.01"))
        neto = (bruto - deduccion).quantize(Decimal("0.01"))
        rows.append(
            LiquidacionDistribucion(
                liquidacion_id=liq.id,
                socia_id=socia.id,
                porcentaje=socia.porcentaje_participacion,
                monto_bruto=bruto,
                deduccion_anticipos=deduccion,
                monto_neto=neto,
                estado_pago=DistribucionEstado.PENDIENTE.value,
            )
        )
        for a in pendientes:
            a.transition_to(AnticipoEstado.DESCONTADO)
            a.liquidacion_id = liq.id
            anticipos_a_descontar.append(a)

    db.add_all(rows)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto al crear la liquidación (código duplicado o descuento concurrente)",
        ) from None
    except Exception:
        db.rollback()
        raise

    db.refresh(liq)
    return liq, warnings


def transicionar_liquidacion(db: Session, liquidacion_id: int, nuevo_estado: str) -> Liquidacion:
    """FSM BORRADOR -> APROBADA -> PAGADA; terminal PAGADA rejects (LIQ-2)."""
    liq = db.get(Liquidacion, liquidacion_id)
    if liq is None:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    try:
        liq.transition_to(LiquidacionEstado(nuevo_estado))
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from e
    db.commit()
    db.refresh(liq)
    return liq


def eliminar_liquidacion(db: Session, liquidacion_id: int) -> None:
    """Delete a BORRADOR liquidacion; children cascade, linked anticipos SET NULL
    (LIQ-1/ANT-2). Non-BORRADOR -> 422 (only draft is editable/deletable)."""
    liq = db.get(Liquidacion, liquidacion_id)
    if liq is None:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    if liq.estado != LiquidacionEstado.BORRADOR.value:
        raise HTTPException(
            status_code=422,
            detail="Solo se puede eliminar una liquidación en BORRADOR",
        )
    db.delete(liq)
    db.commit()


# ---------------------------------------------------------------------------
# v4 — ANT-1/2/3: anticipos
# ---------------------------------------------------------------------------


def crear_anticipo(
    db: Session,
    *,
    socia_id: int,
    monto,
    fecha: date | None = None,
    **extras,
) -> Anticipo:
    """Create an anticipo (ANT-1). Nonexistent socia -> 404/422; monto>0 enforced
    at the schema layer; defaults to PENDIENTE_DESCUENTO."""
    socia = db.get(SociosConfiguracion, socia_id)
    if socia is None:
        raise HTTPException(status_code=404, detail="Socia no encontrada")
    anticipo = Anticipo(
        socia_id=socia_id,
        monto=Decimal(monto),
        fecha=fecha,
        **extras,
    )
    db.add(anticipo)
    try:
        db.commit()
        db.refresh(anticipo)
        return anticipo
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto al crear el anticipo",
        ) from None
    except Exception:
        db.rollback()
        raise


def descontar_anticipo(db: Session, anticipo_id: int, liquidacion_id: int) -> Anticipo:
    """Atomically link an anticipo to a liquidacion and transition to DESCONTADO
    (ANT-2/ANT-3). Double-discount of the same anticipo -> 409 (partial unique +
    FOR UPDATE). ANULADO cannot be discounted (422)."""
    anticipo = db.scalar(
        select(Anticipo).where(Anticipo.id == anticipo_id).with_for_update()
    )
    if anticipo is None:
        raise HTTPException(status_code=404, detail="Anticipo no encontrado")
    if anticipo.estado == AnticipoEstado.ANULADO.value:
        raise HTTPException(status_code=422, detail="Un anticipo ANULADO no se puede descontar")
    if anticipo.estado == AnticipoEstado.DESCONTADO.value or anticipo.liquidacion_id is not None:
        raise HTTPException(status_code=409, detail="El anticipo ya fue descontado")
    liq = db.get(Liquidacion, liquidacion_id)
    if liq is None:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    try:
        anticipo.transition_to(AnticipoEstado.DESCONTADO)
        anticipo.liquidacion_id = liquidacion_id
        db.commit()
        db.refresh(anticipo)
        return anticipo
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto: el anticipo ya fue descontado concurrentemente",
        ) from None
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from e


def transicionar_anticipo(db: Session, anticipo_id: int, nuevo_estado: str) -> Anticipo:
    """FSM PENDIENTE_DESCUENTO -> DESCONTADO|ANULADO; terminal states reject (ANT-2)."""
    anticipo = db.get(Anticipo, anticipo_id)
    if anticipo is None:
        raise HTTPException(status_code=404, detail="Anticipo no encontrado")
    try:
        anticipo.transition_to(AnticipoEstado(nuevo_estado))
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from e
    db.commit()
    db.refresh(anticipo)
    return anticipo


def eliminar_anticipo(db: Session, anticipo_id: int) -> None:
    anticipo = db.get(Anticipo, anticipo_id)
    if anticipo is None:
        raise HTTPException(status_code=404, detail="Anticipo no encontrado")
    db.delete(anticipo)
    db.commit()
