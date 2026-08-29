# Proposal: purge-frontend-mock

## Change
Eliminar todo mock residual del frontend y garantizar que en modo REAL (VITE_USE_MOCK=false) no se muestre ningún dato de atelier.ts.

## Problem
- `Insumos en Alerta / 2 items bajos` viene de `atelier.insumosCriticos` hardcodeado, no de DB
- Dashboard alertas, AppLayout badge, modales AsistenteIa/CompraInsumo/etc usan atelier puro
- Usuario ve datos fantasma aunque /api esté en modo REAL

## Scope
- Audit exhaustivo de src/views/*.vue y src/components/atelier/* (listar cada uso de atelier sin branch isMock)
- Fix InventarioView insumosCriticos → derivado de insumosList (filtro stock < stock_minimo) o /observability/alerts
- Fix DashboardView, AnalisisView, AppLayout
- Fix modales: AsistenteIaModal, CompraInsumoModal, DetalleLiquidacionModal, FichaTallas, GestionSocias, NuevaLiquidacion, NuevaReceta, NuevoAnticipo, etc — branch o migrar a API
- Criterio: en modo REAL, ningún computed/template debe leer atelier sin estar tras isMock

## Non-goals
- Borrar atelier.ts (queda como fallback para VITE_USE_MOCK=true y tests)
- Cambiar layout

## Verify
- VITE_USE_MOCK=false → hard refresh muestra solo datos de /api, sin 2 items bajos fantasma
- Network tab sin datos mock
