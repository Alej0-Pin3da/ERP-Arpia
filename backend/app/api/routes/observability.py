from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.metrics import snapshot
from app.core.deps import get_db, require_roles
from app.models.insumos import Insumo
from app.models.usuarios import Usuario

router = APIRouter(prefix="/observability", tags=["observability"])

audited_user = require_roles("admin", "operador", "consulta")

# NOTE: /summary y /metrics quedan abiertos a propósito: son telemetría de
# infraestructura para scrapers (Prometheus) que no llevan token de usuario.


@router.get("/summary")
def observability_summary():
    return {"metrics": snapshot()}


@router.get("/metrics")
def prometheus_metrics():
    snap = snapshot()
    lines = []
    for path, m in snap.items():
        safe = path.replace("/", "_").replace(":", "").replace("-", "_")
        lines.append(f'http_requests_total{{path=\"{path}\"}} {m["count"]}')
        lines.append(f'http_errors_total{{path=\"{path}\"}} {m["errors"]}')
        lines.append(f'http_latency_avg_ms{{path=\"{path}\"}} {m["avg_ms"]}')
    body = "\n".join(lines) + "\n"
    return Response(content=body, media_type="text/plain")


@router.get("/alerts")
def observability_alerts(db: Session = Depends(get_db), _: Usuario = Depends(audited_user)):
    # Stock crítico real: stock_actual por debajo del mínimo de seguridad.
    rows = (
        db.query(Insumo)
        .filter(Insumo.stock_actual < Insumo.stock_minimo)
        .order_by(Insumo.id)
        .limit(20)
        .all()
    )
    alerts = [
        {
            "type": "stock_critico",
            "insumo_id": r.id,
            "nombre": r.nombre,
            "stock": float(r.stock_actual or 0),
        }
        for r in rows
    ]
    return {"alerts": alerts}
