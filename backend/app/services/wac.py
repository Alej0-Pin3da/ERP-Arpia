from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CompraInsumo, Insumo, Proveedor


def registrar_compra(
    db: Session,
    insumo_id: int,
    proveedor_id: int | None,
    cantidad: str | Decimal,
    precio_unitario: str | Decimal,
    fecha_compra: datetime | None = None,
    commit: bool = True,
) -> CompraInsumo:
    """Register a purchase and recompute the weighted-average cost in one transaction.

    - Locks the insumo row with SELECT ... FOR UPDATE so concurrent purchases of the
      same insumo serialize on the row lock (no lost updates).
    - Computes nuevo_costo = (stock*cost + cantidad*price) / (stock + cantidad) in
      Decimal without rounding; NUMERIC(15,4) storage quantizes at write.
    - ``fecha_compra``: optional timezone-aware datetime (TIMESTAMPTZ). Omitted or
      None keeps the current behavior (server_default ``now()``); an explicit aware
      value is persisted as-is. The WAC formula never uses the date. A naive datetime
      is rejected with TypeError — never persist an ambiguous timestamp.
    - ``commit=True`` (default) commits atomically; ``commit=False`` leaves the
      caller in control of the transaction (used by historical batch loads).
      On any failure rolls back and re-raises.
    """
    if fecha_compra is not None and fecha_compra.tzinfo is None:
        raise TypeError(
            "fecha_compra must be timezone-aware (TIMESTAMPTZ column); "
            "got a naive datetime. Pass an aware datetime or None for server_default now()."
        )

    cantidad_dec = Decimal(str(cantidad))
    precio_dec = Decimal(str(precio_unitario))

    try:
        insumo = db.scalar(select(Insumo).where(Insumo.id == insumo_id).with_for_update())
        if insumo is None:
            raise HTTPException(status_code=404, detail="Insumo not found")

        if proveedor_id is not None:
            proveedor = db.get(Proveedor, proveedor_id)
            if proveedor is None:
                raise HTTPException(status_code=400, detail="Proveedor does not exist")

        stock = insumo.stock_actual
        costo = insumo.costo_promedio_actual
        nuevo_costo = (stock * costo + cantidad_dec * precio_dec) / (stock + cantidad_dec)

        insumo.stock_actual = stock + cantidad_dec
        insumo.costo_promedio_actual = nuevo_costo

        compra = CompraInsumo(
            insumo_id=insumo_id,
            proveedor_id=proveedor_id,
            cantidad_comprada=cantidad_dec,
            precio_unitario_compra=precio_dec,
            fecha_compra=fecha_compra,
        )
        db.add(compra)
        if commit:
            db.commit()
            db.refresh(compra)
        return compra
    except IntegrityError:
        # FK/constraint violation (e.g. concurrent insumo deletion) -> no 500 leak.
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicting purchase state; the purchase was not registered",
        ) from None
    except Exception:
        db.rollback()
        raise
