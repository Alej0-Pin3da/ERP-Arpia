# Tasks: compras-wac-ux — Registrar Compra WAC with Live Simulation & History

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 650–750 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 Backend → PR2 Frontend core → PR3 Wiring+tests |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend WAC SSOT (schemas/models/migration/service/routes) | PR1 | `pytest backend/tests/test_wac.py backend/tests/test_compras_insumos.py -q` | `POST /api/v1/compras-insumos` TOTAL/UNIT curl Docker PG | Revert migration + 4 BE files |
| 2 | Frontend preview+history (utils/ComprasForm/HistorialDrawer CSV) | PR2 | `npm run test -- compras-form.spec historial-drawer.spec` | Toggle TOTAL/UNIT, verify live preview | Revert 3 FE files |
| 3 | Wiring+verification (InventarioView/endpoints/full suite) | PR3 | `pytest backend/tests -q && npm run test` | InventarioView operador/consulta + concurrent POSTs | Revert InventarioView+endpoints |

## Phase 1: Foundation

- [x] 1.1 `backend/app/schemas/compra_insumo.py` — add `modo TOTAL|UNIT`, `costo_total? gt0`, `factura? ≤100`, `proveedor_id?`, finite check, extend `Read` with `costo_unitario_aplicado` Numeric(15,4) → REQ-CI-001/002 SCN-CI-001/004
- [x] 1.2 `backend/app/models/insumos.py` — add `CompraInsumo.proveedor_id FK SET NULL nullable`, `factura`, `costo_unitario_aplicado` Numeric(15,4), index `fecha_compra` → REQ-CI-001
- [x] 1.3 `backend/alembic/versions/*_compras_wac_ux.py` — nullable cols + index, backfill NULL, downgrade drops → idempotent

## Phase 2: Core Implementation

- [x] 2.1 `backend/app/services/wac.py` — handle `modo/costo_total/factura/proveedor_id`, `price=costo_total/qty` Decimal if TOTAL, keep `SELECT FOR UPDATE` + atomic commit/rollback, `commit=False` → REQ-WAC-001/002/004 SCN-WAC-001/002
- [x] 2.2 `backend/app/api/routes/compras_insumos.py` — pass new fields, gate `gt0/isFinite→422`, 404 insumo/400 proveedor, force `fecha_compra DESC` → REQ-CI-001/003 SCN-CI-002/003
- [x] 2.3 `frontend/src/utils/inventario.ts` — extend `CompraPayloadInput`, update `buildCompraPayload` TOTAL branch, add `buildHistorialCsv` + `CSV_HEADER` → REQ-CI-003 REQ-WAC-003
- [x] 2.4 `frontend/src/components/inventario/ComprasForm.vue` — TOTAL/UNIT toggle, `computed newStock/newWAC/valuation` mirroring `(stock*cost+qty*unit)/newStock`, disable Confirm if `qty<=0||cost<=0||!isFinite` → REQ-WAC-003 SCN-WAC-004

## Phase 3: Integration / Wiring

- [x] 3.1 `frontend/src/components/inventario/HistorialDrawer.vue` — Drawer: date/qty/prev→new stock/cost/total/factura + CSV → REQ-CI-003 SCN-CI-005
- [ ] 3.2 `frontend/src/views/InventarioView.vue` — per-row `+ Compra` (pre-filled) + `History`, hide `+ Compra` for consulta → REQ-CI-004 SCN-CI-006
- [x] 3.3 `frontend/src/api/endpoints.ts` — typed `comprasApi` for new fields → REQ-CI-002

## Phase 4: Testing

- [ ] 4.1 `backend/tests/test_wac.py` — TOTAL→unit, zero-stock `nuevo==price`, stable 5.0000, 4 decimals, `commit=False` → SCN-WAC-001/002/003
- [ ] 4.2 `backend/tests/test_compras_insumos.py` — POST TOTAL 201 cost7.0000+factura, 422 Infinity/NaN/qty<=0 no write, 404/400 FK, GET DESC, RBAC consulta GET200 POST403 → SCN-CI-001..005
- [ ] 4.3 Concurrent threaded `pytest` same-insumo serializes no lost update, distinct parallelizes on Docker PG → SCN-WAC-005 REQ-WAC-004
- [ ] 4.4 `vitest compras-form.spec.ts/historial-drawer.spec.ts` — parity 10@5+10@9→7.0000, toggle recalc, disabled gate, CSV header `fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura` → SCN-WAC-004 SCN-CI-005

## Phase 5: Verification & Cleanup

- [ ] 5.1 `pytest backend/tests -q` green + `npm run build`, verify no FLOAT, `NUMERIC(15,4)`, `/api/v1`
- [ ] 5.2 Manual: seed 10@5, POST TOTAL90, preview=backend 7.0000, History prev→new + CSV, RBAC check
- [ ] 5.3 Remove dead code, confirm `ComprasTable` sort with DESC default
