"""WooCommerce order webhook (V6 M3).

A validated ``order.created`` event becomes a REAL web-channel sale through
``registrar_venta`` — stock explosion, finished units, cost snapshots and
the M2 profit split all run unchanged. Made-to-order needs nothing special:
with no finished units on hand the sale consumes raw insumos via the
standard explosion (409 when nothing covers it, so Woo retries on restock).

Security: HMAC-SHA256 (base64) over the raw body, compared in constant
time. No secret configured -> 503 (fail closed). Idempotency: one row per
(order id); duplicates ack with the original sale, concurrent doubles are
rejected by the UNIQUE pair and re-read.
"""

import base64
import hashlib
import hmac
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.productos import Producto
from app.models.webhook import WebhookEvento
from app.services.inventory import registrar_venta

SOURCE = "woo"


def firma_valida(secret: str, body: bytes, signature: str | None) -> bool:
    """Constant-time check of WooCommerce's X-WC-Webhook-Signature."""
    if not secret or not signature:
        return False
    esperada = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(esperada, signature)


def _ya_procesado(db: Session, external_id: str) -> WebhookEvento | None:
    return db.scalar(
        select(WebhookEvento).where(
            WebhookEvento.source == SOURCE,
            WebhookEvento.external_id == external_id,
        )
    )


def procesar_orden_woo(db: Session, order: dict) -> dict:
    """Turn a Woo order dict into a web sale (idempotent by order id)."""
    external_id = str(order.get("id") or "")
    if not external_id:
        raise HTTPException(status_code=422, detail="Orden sin id")
    items = order.get("line_items") or []
    if not items:
        raise HTTPException(status_code=422, detail="Orden sin line_items")

    existente = _ya_procesado(db, external_id)
    if existente is not None and existente.venta_id is not None:
        return {"venta_id": existente.venta_id, "duplicado": True}

    detalles = []
    for item in items:
        sku = str(item.get("sku") or "").strip()
        if not sku:
            raise HTTPException(status_code=422, detail="Línea sin SKU")
        producto = db.scalar(select(Producto).where(Producto.codigo == sku))
        if producto is None:
            raise HTTPException(
                status_code=422, detail=f"SKU desconocido: {sku}"
            )
        cantidad = Decimal(str(item.get("quantity") or "0"))
        if cantidad <= 0:
            raise HTTPException(status_code=422, detail=f"Cantidad inválida para {sku}")
        detalles.append(
            {
                "producto_id": producto.id,
                "variante_id": None,
                "cantidad": cantidad,
                "precio_unitario": Decimal(str(item.get("price") or "0")),
            }
        )

    venta = registrar_venta(
        db,
        {
            "canal_venta": "web",
            "detalles": detalles,
            "observaciones": f"WooCommerce orden {external_id}",
        },
    )
    try:
        db.add(
            WebhookEvento(
                source=SOURCE, external_id=external_id, venta_id=venta.id
            )
        )
        db.commit()
    except IntegrityError:
        # Concurrent duplicate won the race: ack with the winner's sale.
        db.rollback()
        existente = _ya_procesado(db, external_id)
        if existente is not None and existente.venta_id is not None:
            return {"venta_id": existente.venta_id, "duplicado": True}
        raise
    db.refresh(venta)
    return {"venta_id": venta.id, "duplicado": False}
