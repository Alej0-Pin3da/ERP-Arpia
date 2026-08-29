# Spec: metrics-observability

## Scenarios
1. GET /api/v1/metrics returns Prometheus exposition or JSON summary with per-endpoint latency/count
2. Stock crítico: GET /api/v1/observability/alerts returns insumos bajo mínimo
3. Health: GET /health/ready checks DB and Redis (if configured), returns 200/503

## Requirements
- Middleware no debe afectar latencia >2ms
- Métricas en memoria con reset opcional, no persistidas
- Sin dependencias nuevas pesadas si es posible
