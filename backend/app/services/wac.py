from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CompraInsumo, Insumo


def registrar_compra(
    db: Session,
    insumo_id: int,
    cantidad: str | Decimal,
    precio_unitario: str | Decimal | None = None,
    costo_total: str | Decimal | None = None,
    modo: str = "UNIT",
    factura: str | None = None,
    proveedor_id: int | None = None,
    fecha_compra: datetime | None = None,
    commit: bool = True,
) -> CompraInsumo:
    """Register a purchase and recompute the weighted-average cost in one transaction.

    - Locks the insumo row with SELECT ... FOR UPDATE so concurrent purchases of the
      same insumo serialize on the row lock (no lost updates).
    - Computes nuevo_costo = (stock*cost + cantidad*price) / (stock + cantidad) in
      Decimal without rounding; NUMERIC(15,4) storage quantizes at write.
    - ``modo`` TOTAL derives ``price=costo_total/qty`` in Decimal before WAC.
    - ``factura`` and ``proveedor_id`` are stored nullable for history/CSV.
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
    # Finite guard at service layer (defense in depth; schema also validates)
    if not cantidad_dec.is_finite():
        raise HTTPException(status_code=422, detail="cantidad_comprada must be finite")

    modo_norm = (modo or "UNIT").upper()
    if modo_norm not in ("UNIT", "TOTAL"):
        raise HTTPException(status_code=422, detail="modo must be TOTAL or UNIT")

    if modo_norm == "TOTAL":
        if costo_total is None:
            raise HTTPException(status_code=422, detail="costo_total required for TOTAL modo")
        costo_total_dec = Decimal(str(costo_total))
        if not costo_total_dec.is_finite():
            raise HTTPException(status_code=422, detail="costo_total must be finite")
        if costo_total_dec <= 0:
            raise HTTPException(status_code=422, detail="costo_total must be > 0")
        if cantidad_dec <= 0:
            raise HTTPException(status_code=422, detail="cantidad_comprada must be > 0")
        precio_dec = costo_total_dec / cantidad_dec
    else:
        if precio_unitario is None:
            raise HTTPException(status_code=422, detail="precio_unitario required for UNIT modo")
        precio_dec = Decimal(str(precio_unitario))
        if not precio_dec.is_finite():
            raise HTTPException(status_code=422, detail="precio_unitario must be finite")
        if cantidad_dec <= 0 or precio_dec < 0:
            # cantidad handled by gt0 in schema; keep service guard
            raise HTTPException(status_code=422, detail="cantidad and precio must be valid")

    factura_clean = factura.strip() if factura and factura.strip() else None
    if factura_clean and len(factura_clean) > 100:
        raise HTTPException(status_code=422, detail="factura max length 100")

    try:
        insumo = db.scalar(select(Insumo).where(Insumo.id == insumo_id).with_for_update())
        if insumo is None:
            raise HTTPException(status_code=404, detail="Insumo not found")

        stock = insumo.stock_actual
        costo = insumo.costo_promedio_actual
        nuevo_costo = (stock * costo + cantidad_dec * precio_dec) / (stock + cantidad_dec)

        insumo.stock_actual = stock + cantidad_dec
        insumo.costo_promedio_actual = nuevo_costo

        compra = CompraInsumo(
            insumo_id=insumo_id,
            cantidad_comprada=cantidad_dec,
            precio_unitario_compra=precio_dec,
            costo_unitario_aplicado=nuevo_costo,
            factura=factura_clean,
            proveedor_id=proveedor_id,
            fecha_compra=fecha_compra,
        )
        db.add(compra)
        if commit:
            db.commit()
            db.refresh(compra)
        return compra
    except HTTPException:
        db.rollback()
        raise
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
