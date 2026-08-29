# Proposal: metrics-observability

## Change
metrics-observability — Métricas por endpoint + alertas + health checks completos.

## Scope
- Middleware de métricas (latencia p50/p95, count, error rate por endpoint)
- Endpoint GET /api/v1/metrics (Prometheus text) o /api/v1/observability/summary (JSON)
- Alertas: stock crítico, margen anormal, pérdidas (job o endpoint)
- Health /ready ampliado (DB + Redis opcional)
- Dashboard frontend mínimo o panel en AnalisisView

## Non-goals
- APM externo (Datadog/NewRelic)
- Logging ya existe (RequestContextMiddleware)

## Alternatives
- prometheus_client vs contador en memoria con agregación simple (elegir según deps)
