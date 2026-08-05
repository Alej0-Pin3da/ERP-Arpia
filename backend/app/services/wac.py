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
) -> CompraInsumo:
    """Register a purchase and recompute the weighted-average cost in one transaction.

    - Locks the insumo row with SELECT ... FOR UPDATE so concurrent purchases of the
      same insumo serialize on the row lock (no lost updates).
    - Computes nuevo_costo = (stock*cost + cantidad*price) / (stock + cantidad) in
      Decimal without rounding; NUMERIC(15,4) storage quantizes at write.
    - Commits atomically (single commit); on any failure rolls back and re-raises.
    """
    cantidad_dec = Decimal(str(cantidad))
    precio_dec = Decimal(str(precio_unitario))

    try:
        insumo = db.scalar(
            select(Insumo).where(Insumo.id == insumo_id).with_for_update()
        )
        if insumo is None:
            raise HTTPException(status_code=404, detail="Insumo not found")

        if proveedor_id is not None:
            proveedor = db.get(Proveedor, proveedor_id)
            if proveedor is None:
                raise HTTPException(status_code=400, detail="Proveedor does not exist")

        stock = insumo.stock_actual
        costo = insumo.costo_promedio_actual
        nuevo_costo = (stock * costo + cantidad_dec * precio_dec) / (
            stock + cantidad_dec
        )

        insumo.stock_actual = stock + cantidad_dec
        insumo.costo_promedio_actual = nuevo_costo

        compra = CompraInsumo(
            insumo_id=insumo_id,
            proveedor_id=proveedor_id,
            cantidad_comprada=cantidad_dec,
            precio_unitario_compra=precio_dec,
        )
        db.add(compra)
        db.commit()
        db.refresh(compra)
        return compra
    except IntegrityError:
        # FK/constraint violation (e.g. concurrent insumo deletion) -> no 500 leak.
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicting purchase state; the purchase was not registered",
        )
    except Exception:
        db.rollback()
        raise
