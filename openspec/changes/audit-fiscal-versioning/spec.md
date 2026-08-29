# Spec: audit-fiscal-versioning

## Scenarios
1. POST /precio-versions con fecha crea versión; GET lista por producto ordenado por fecha
2. Cierre mensual: POST /cierres {periodo: 2026-08} bloquea; intento de editar venta en período cerrado → 409
3. GET /cierres lista cierres con estado

## Requirements
- Migraciones Alembic reversibles
- Validación en services de ventas/finanzas consulta cierres
