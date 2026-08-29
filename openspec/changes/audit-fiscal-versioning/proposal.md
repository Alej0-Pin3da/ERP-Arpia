# Proposal: audit-fiscal-versioning

## Change
Versionado de precios/costos por fecha + cierres mensuales + traza BOM.

## Scope
- Tablas `precio_versions`, `costo_versions` (producto/variante, fecha_desde, precio/costo, usuario)
- Tabla `cierres_mensuales` (periodo YYYY-MM, estado, cerrado_por, fecha)
- Validación: no editar ventas/movimientos en período cerrado
- Endpoints: GET/POST precio_versions, costo_versions, cierres
- Auditoría BOM: log de cambios en bom_insumos/bom_productos

## Non-goals
- Facturación electrónica AFIP
- Reportes contables externos
