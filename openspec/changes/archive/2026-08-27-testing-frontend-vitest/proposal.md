# Proposal: testing-frontend-vitest

## Change
testing-frontend-vitest — Vitest specs para flujos críticos del frontend (gap Sprint 3).

## Context
Frontend con 0 specs reales (vitest configurado pero sin tests). Backend ya tiene 605+ tests. Riesgo: regresiones no detectadas en Ventas/Inventario/Finanzas/Auth.

## Scope
- Setup Vitest + Testing Library + Pinia + Vue Router mocks
- Specs: VentasView, InventarioView/Insumos, FinanzasView, Auth/login, composables useMode/useClientes/useVentas, services/api client
- Fixtures y helpers reutilizables
- CI: npm test en pipeline

## Non-goals
- E2E Playwright (fase posterior)
- Visual regression / design system
- Cambios de UI

## Acceptance
- `npm test` con coverage sobre flujos críticos
- Al menos 30-40 specs verdes sin flakiness
- CI no pasa si tests fallan
