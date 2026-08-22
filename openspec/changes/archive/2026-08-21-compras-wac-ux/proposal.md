# Proposal: compras-wac-ux — Registrar Compra WAC with Live Simulation & History

## Intent
Port Atelier rev.3 WAC UX (live simulation, TOTAL/UNIT toggle, history) onto ERP-Arpia's transactional backend. `POST /compras-insumos` + `registrar_compra` (SELECT FOR UPDATE, `NUMERIC(15,4)`) works but has no guided UX. Phase 2 per `ATELIER_PORT_TRACKING.md §5`. Users: **operador** (fast TOTAL entry + preview), **admin** (audit), **consulta** (read-only).

## Scope
### In Scope
- Backend: extend `CompraInsumoCreate` with `modo TOTAL|UNIT` + `factura`/`proveedor_id`; SSOT `registrar_compra`, Decimal WAC, atomic commit.
- Frontend: `ComprasForm.vue` toggle + live `computed` (newStock/newWAC/valuation), Confirm disabled if `qty<=0||cost<=0`.
- Frontend: `HistorialDrawer.vue` per-insumo (date, qty, prev→new stock/cost, total, factura) + CSV.
- Wire `InventarioView.vue` actions `+ Compra`/`History`; zero-stock + Infinity guards.

### Out of Scope
- Phases 3-5: Dashboard, BOM Sheet, Kanban 8, Clientes medidas, Optimizador, Cotizador.
- WAC trigger, Firebase/AI, design tokens (Phase 1), bulk import, `fecha_compra` range filter.

## Capabilities
### New Capabilities
- None

### Modified Capabilities
- `compras-insumos`: Create/Read (modo, factura/proveedor), history UX.
- `wac-engine`: live-simulation contract (preview display-only; backend authoritative).

## Approach
Service-centric (no trigger): `TOTAL→ unit=total/qty` then `(stock*cost+qty*price)/(stock+qty)`. Frontend `computed` mirrors formula (`costValue=unitCost*10` default). History reuses `GET /compras-insumos?insumo_id`. Trigger hides logic, needs lock anyway and hurts tests — service keeps explicit txn + `commit=False` for batches.

## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/schemas/compra_insumo.py` | Modified | modo, factura, proveedor_id |
| `backend/app/services/wac.py` | Modified | TOTAL conversion |
| `backend/app/api/routes/compras_insumos.py` | Modified | Pass new fields |
| `backend/app/models/insumos.py` | Modified | cols + index (if missing) |
| `frontend/src/components/inventario/ComprasForm.vue` | Modified | Toggle + simulation |
| `frontend/src/components/inventario/HistorialDrawer.vue` | New | History + CSV |
| `frontend/src/views/InventarioView.vue` | Modified | Actions column |

## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Lost update concurrent | Med | SELECT FOR UPDATE + test |
| TOTAL/UNIT drift | Med | Backend authoritative; shared test |
| Precision `toFixed(2)` | Low | NUMERIC(15,4); round display only |
| >800 lines | Low | 3 slices <250 lines |
| `qty<=0→Infinity` | Low | Disable Confirm + `gt0` |

## Rollback Plan
Revert migration + schema/route + `ComprasForm.vue`. No data loss; single commit.

## Dependencies
- `registrar_compra` + RBAC `admin/operador` (done); PrimeVue; Alembic/PostgreSQL Docker; `pytest backend/tests -q`.

## Success Criteria
- [ ] POST TOTAL/UNIT updates stock/cost per WAC; zero-stock → newCost=unitPrice
- [ ] Preview matches backend to 4 decimals (10@5+10@9→7.0000)
- [ ] Confirm disabled + 422 on invalid; no write
- [ ] History prev→new + factura; RBAC respected
- [ ] Concurrent test passes; `pytest -q` green; ≤800 lines; `/api/v1` + NUMERIC ok
