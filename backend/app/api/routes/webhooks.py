"""Inbound webhooks router (V6 M3).

No session auth here — the HMAC signature IS the auth. Fail closed when
the secret is not configured.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db
from app.services import webhooks as webhooks_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/woo/order-created", status_code=status.HTTP_200_OK)
async def woo_order_created(request: Request, db: Session = Depends(get_db)):
    """Accept a WooCommerce order.created event as a web sale."""
    if not settings.WOO_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook no configurado")
    body = await request.body()
    firma = request.headers.get("X-WC-Webhook-Signature")
    if not webhooks_service.firma_valida(settings.WOO_WEBHOOK_SECRET, body, firma):
        raise HTTPException(status_code=401, detail="Firma inválida")
    try:
        order = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="JSON inválido") from None
    if not isinstance(order, dict):
        raise HTTPException(status_code=422, detail="Orden inválida")
    return webhooks_service.procesar_orden_woo(db, order)
