"""Finanzas engine — financial movements, partner-config and settlements.

Owns the business rules the DB cannot express: the multi-row invariant
"sum of partner participation == 100" is validated here at the service layer
(create requires an exact 100 total; updates may rebalance *below* 100 while
another partner completes validation, but never above), and settlements are
one-time per ``liquidacion_id`` (the partial unique index is the last line of
defense; the service rejects replays with 409 before writing).
"""

import secrets
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.finanzas import MovimientoFinanciero, SociosConfiguracion


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
        )
    except Exception:
        db.rollback()
        raise


def listar_movimientos(
    db: Session, estado: str = "activo"
) -> list[MovimientoFinanciero]:
    """List movements ordered by id, filtered by estado (soft-delete aware)."""
    stmt = (
        select(MovimientoFinanciero)
        .where(MovimientoFinanciero.estado == estado)
        .order_by(MovimientoFinanciero.id)
    )
    return list(db.scalars(stmt))


def eliminar_movimiento(db: Session, movimiento_id: int) -> MovimientoFinanciero:
    """Soft delete a movement (estado -> 'inactivo')."""
    movimiento = db.get(MovimientoFinanciero, movimiento_id)
    if movimiento is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    movimiento.estado = "inactivo"
    db.commit()
    db.refresh(movimiento)
    return movimiento


def actualizar_movimiento(
    db: Session, movimiento_id: int, payload: dict
) -> MovimientoFinanciero:
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
    if movimiento is None or movimiento.estado != "activo":
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
            select(MovimientoFinanciero).where(
                MovimientoFinanciero.liquidacion_id.like(f"{key}%")
            )
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
        )
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
    socio = SociosConfiguracion(
        nombre=nombre, porcentaje_participacion=porcentaje
    )
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
        )
    except Exception:
        db.rollback()
        raise


def actualizar_socio_configuracion(db: Session, socio_id: int, porcentaje: Decimal) -> SociosConfiguracion:
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
