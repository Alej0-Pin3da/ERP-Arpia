from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.metrics import snapshot
from app.core.deps import get_db

router = APIRouter(prefix="/observability", tags=["observability"])


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
def observability_alerts(db: Session = Depends(get_db)):
    from sqlalchemy import text
    # stock crítico: insumos con stock < 10
    try:
        rows = db.execute(text("SELECT id, nombre, stock FROM insumos WHERE stock < 10 LIMIT 20")).mappings().all()
        alerts = [{"type": "stock_critico", "insumo_id": r["id"], "nombre": r["nombre"], "stock": float(r["stock"])} for r in rows]
    except Exception:
        alerts = []
    return {"alerts": alerts}
