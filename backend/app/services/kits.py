"""Kit costing — always live, never stored.

A kit's total cost is the sum over its lines of
``calcular_costo_produccion(producto) * cantidad`` (recursive BOM math, the
same function production uses), so kits track cost movements automatically.
The promo margin (utility over promo price) fires a visual alert below the
5% safety floor (``MARGEN_SEGURIDAD_KIT``) — alert, never a block.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kits import MARGEN_SEGURIDAD_KIT, Kit, KitProducto
from app.models.productos import Producto
from app.services.costos import calcular_costo_produccion


def costear_kit(db: Session, kit: Kit) -> dict:
    """Live cost/margin snapshot for a kit (pure read, no writes)."""
    total = Decimal("0")
    lineas = []
    for linea in kit.lineas:
        unitario = calcular_costo_produccion(db, linea.producto_id)
        subtotal = unitario * Decimal(linea.cantidad)
        total += subtotal
        lineas.append(
            {
                "id": linea.id,
                "producto_id": linea.producto_id,
                "producto_nombre": linea.producto.nombre if linea.producto else None,
                "cantidad": linea.cantidad,
                "costo_unitario": unitario,
                "subtotal": subtotal,
            }
        )
    precio = Decimal(kit.precio_promocional)
    if precio > 0:
        margen = ((precio - total) / precio * Decimal("100")).quantize(Decimal("0.01"))
    else:
        margen = Decimal("0.00")
    return {
        "costo_total": total,
        "margen_pct": margen,
        "alerta_margen": bool(margen < MARGEN_SEGURIDAD_KIT),
        "lineas": lineas,
    }


def obtener_kit(db: Session, kit_id: int) -> Kit:
    kit = db.get(Kit, kit_id)
    if kit is None:
        raise HTTPException(status_code=404, detail="Kit no encontrado")
    return kit


def crear_kit(db: Session, nombre: str, precio_promocional: Decimal) -> Kit:
    kit = Kit(nombre=nombre, precio_promocional=precio_promocional)
    db.add(kit)
    db.commit()
    db.refresh(kit)
    return kit


def agregar_linea(db: Session, kit: Kit, producto_id: int, cantidad: Decimal) -> KitProducto:
    if db.get(Producto, producto_id) is None:
        raise HTTPException(status_code=422, detail="producto_id no existe")
    if db.scalar(
        select(KitProducto).where(
            KitProducto.kit_id == kit.id, KitProducto.producto_id == producto_id
        )
    ) is not None:
        raise HTTPException(status_code=409, detail="El producto ya está en el kit")
    linea = KitProducto(kit_id=kit.id, producto_id=producto_id, cantidad=cantidad)
    db.add(linea)
    db.commit()
    db.refresh(linea)
    return linea
