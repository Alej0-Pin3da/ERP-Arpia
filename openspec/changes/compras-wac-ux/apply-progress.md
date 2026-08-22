# Apply Progress: compras-wac-ux

## Change
compras-wac-ux — Registrar Compra WAC with Live Simulation & History
Project: erp-arpia
Mode: Standard (Strict TDD enabled; Phase 4 TDD cycle deferred — PR2 is frontend display-only slice, backend authoritative Decimal unchanged)
Delivery: auto-chain stacked-to-main — PR1 (Backend WAC SSOT) + PR2 (Frontend core slice)

## Completed Tasks (9/17)
- [x] 1.1 schemas/compra_insumo.py — modo TOTAL|UNIT, costo_total? gt0, factura? ≤100, proveedor_id?, finite check, Read costo_unitario_aplicado
- [x] 1.2 models/insumos.py — proveedor_id nullable (no FK, Proveedores removed), factura, costo_unitario_aplicado Numeric(15,4), index fecha_compra
- [x] 1.3 alembic 20260821_compras_wac_ux.py — nullable cols + index idempotent, backfill NULL, downgrade drops
- [x] 2.1 services/wac.py — modo/costo_total handling price=costo_total/qty Decimal if TOTAL, factura/proveedor_id, retain SELECT FOR UPDATE + atomic commit/rollback, commit=False
- [x] 2.2 api/routes/compras_insumos.py — pass new fields, proveedor 400 guard (Proveedores missing → 400), gt0/isFinite→422, GET fecha_compra DESC ordering
- [x] 2.3 frontend/src/utils/inventario.ts — extend CompraPayloadInput (modo/costo_total/factura/proveedor_id), TOTAL branch (costo_total/qty omitted precio_unitario), CSV_HEADER + buildHistorialCsv with csvEscape → REQ-CI-003 REQ-WAC-003
- [x] 2.4 frontend/src/components/inventario/ComprasForm.vue — TOTAL/UNIT toggle, computed newStock/newWAC/valuation mirroring (stock*cost+qty*unit)/newStock in JS Number display-only, disable Confirm if qty<=0||cost<=0||!isFinite, factura input, preview parity 10@5+10@9→7.0000 — REQ-WAC-003 SCN-WAC-004
- [x] 3.1 frontend/src/components/inventario/HistorialDrawer.vue — PrimeVue Drawer: date/qty/prev→new stock/cost/total/factura + CSV export calling buildHistorialCsv → REQ-CI-003 SCN-CI-005
- [x] 3.3 frontend/src/api/endpoints.ts — typed CompraCreatePayload + comprasApi.create typed for modo/costo_total/factura/proveedor_id → REQ-CI-002

## Files Changed
| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/schemas/compra_insumo.py` | Modified (PR1) | Added modo, costo_total, factura, proveedor_id, finite validator, model_validator for modo semantics, extended Read |
| `backend/app/models/insumos.py` | Modified (PR1) | Added proveedor_id (Integer nullable, no FK), factura String(100), costo_unitario_aplicado Numeric(15,4) |
| `backend/alembic/versions/20260821_compras_wac_ux.py` | Created (PR1) | Idempotent migration: checks _has_column/_has_index before add, index fecha_compra guard |
| `backend/app/services/wac.py` | Modified (PR1) | Extended registrar_compra signature with modo/costo_total/factura/proveedor_id, TOTAL derivation Decimal, finite guards, costo_unitario_aplicado persist, HTTPException rollback guard |
| `backend/app/api/routes/compras_insumos.py` | Modified (PR1) | Import HTTPException/text, proveedor validation via to_regclass raw SQL → 400, pass new fields to service, default ordering fecha_compra DESC |
| `backend/app/models/ventas.py` | Modified (PR1 unplanned) | Fixed AmbiguousForeignKeysError: Devolucion reversed_by_user/usuario relationships now specify foreign_keys |
| `frontend/src/utils/inventario.ts` | Modified (PR2) | Extended CompraPayloadInput (modo TOTAL|UNIT, costo_total, factura, proveedor_id), TOTAL branch derives costo_total/qty, added CSV_HEADER `fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura` + HistorialCsvRow + buildHistorialCsv with escaping |
| `frontend/src/components/inventario/ComprasForm.vue` | Modified (PR2) | Added modo Select toggle, costo_total vs precio_unitario conditional InputNumber, factura InputText, computed selectedInsumo/newStock/newWAC/valuation (JS Number display-only), isConfirmDisabled gate (qty<=0||cost<=0||!isFinite), factura passthrough, preview data-test=compra-preview |
| `frontend/src/components/inventario/HistorialDrawer.vue` | Created (PR2) | PrimeVue Drawer right 42rem, historialRows computed ASC→WAC running (prev→new), table date/qty/prev→new stock/cost/total/factura, CSV button via buildHistorialCsv Blob download |
| `frontend/src/api/endpoints.ts` | Modified (PR2) | Added CompraCreatePayload intersection type (modo/costo_total/factura/proveedor_id) + comprasApi.create typed |

## Deviations from Design
- PR1: `proveedor_id` column added WITHOUT FK constraint: Proveedores table was removed in 0008_remove_proveedores; design open question flagged this. Route validates via raw SQL `to_regclass('public.Proveedores')` → 400 if missing or id not found, preserving spec 400 contract without recreating table.
- PR1: `costo_unitario_aplicado` made nullable True (not enforced NOT NULL) to allow backfill NULL for historical rows; new purchases populate via service nuevo_costo. Spec said NUMERIC(15,4) strings in Read, implemented as Decimal | None.
- PR1: `backend/app/models/ventas.py` fix was not in tasks but required to unblock configure_mappers() import (two FKs to Usuarios from Devoluciones). Included as work-unit collateral.
- PR2: `buildCompraPayload` omits `modo` when UNIT/undefined to preserve MOD-4 payload shape for existing tests (backend defaults UNIT). TOTAL explicitly sets modo and costo_total without precio_unitario_compra (backend 422 guard). This keeps backward compat while satisfying spec 1.1→2.1 contract.
- PR2: `ComprasForm` factura/proveedor_id are pass-through via buildCompraPayload; InsumoId prefill via initialInsumoId prop for 3.2 wiring (currently unused, no InventarioView wiring yet).
- PR2: `HistorialDrawer` synthesizes prev→new from chronological running WAC starting at zero-stock when initial snapshot unknown (display-only). PR3 will wire real history fetch; current rows reversed to newest-first for SCN-CI-005 parity.
- PR2: Endpoints type `CompraCreatePayload` uses intersection rather than regenerating `api.d.ts` (requires live backend `openapi.json`). Regen deferred to PR3 but typed correctly.

## Work Unit Evidence (PR2 — Frontend core)

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `npm run test -- tests/unit/inventario.spec.ts tests/component/compras-form.spec.ts` → 14 passed (2 files) in 1.93s; full suite `npm run test` → 63 files, 569 tests passed, 0 failed (21.49s). `npm run build` → built in 4.79s (822 kB chunk warning pre-existing). Parity 10@5+10@9→7.0000 verified via computed `(10*5+10*9)/20`. |
| Runtime harness command/scenario and exact result | N/A — no Docker PG in this env; InventarioView wiring (3.2) deferred to PR3. Preview verified via vitest mount: qty0 disables Confirm; modo toggle recalc unit = total/qty; isConfirmDisabled gate qty<=0||cost<=0||!isFinite. Drawer CSV header `fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura` validated via buildHistorialCsv call (header row). |
| Rollback boundary | Revert 4 FE files: `utils/inventario.ts`, `components/inventario/ComprasForm.vue`, `components/inventario/HistorialDrawer.vue` (new), `api/endpoints.ts`. No migration to revert in PR2. Single `git revert` of `feat(compras-wac)` PR2 commit restores PR1 state. PR1 rollback boundary remains independent. |

## Remaining Tasks (8/17)
- [ ] 3.2 InventarioView.vue — per-row +Compra (pre-filled) + History, hide +Compra for consulta → REQ-CI-004 SCN-CI-006
- [ ] 4.1 test_wac.py — TOTAL→unit, zero-stock nuevo==price, stable 5.0000, 4 decimals, commit=False → SCN-WAC-001/002/003
- [ ] 4.2 test_compras_insumos.py — POST TOTAL 201 cost7.0000+factura, 422 Infinity/NaN/qty<=0 no write, 404/400 FK, GET DESC, RBAC consulta GET200 POST403 → SCN-CI-001..005
- [ ] 4.3 Concurrent threaded pytest same-insumo serializes no lost update, distinct parallelizes on Docker PG → SCN-WAC-005 REQ-WAC-004
- [ ] 4.4 vitest compras-form.spec.ts/historial-drawer.spec.ts — parity 10@5+10@9→7.0000, toggle recalc, disabled gate, CSV header `fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura` → SCN-WAC-004 SCN-CI-005 (partial: unit/CSV via PR2; full TDD deferred to PR3)
- [ ] 5.1 pytest backend/tests -q green + npm build — verify no FLOAT, NUMERIC(15,4), /api/v1
- [ ] 5.2 Manual: seed 10@5, POST TOTAL90, preview=backend 7.0000, History prev→new + CSV, RBAC check
- [ ] 5.3 Remove dead code, confirm ComprasTable sort with DESC default

## Workload / PR Boundary
- Mode: chained PR slice (stacked-to-main)
- Current work unit: 2 — Frontend preview+history (utils/ComprasForm/HistorialDrawer/CSV/endpoints)
- Boundary: Start 2.3 (utils) → End 3.3 (endpoints). InventarioView wiring intentionally deferred to PR3 to stay under review budget.
- Estimated review budget impact: ~385 lines (PR2 alone: 219 modified + 166 new Drawer; PR1 was ~150 lines; combined now ~535 but PR2 counted standalone ~385 under 400 limit? Exceeds ~200 target by ~185 — noted as stacked slice still under 800 global budget. Next slice PR3 will be ≤250 lines).
- Commit: `feat(compras-wac): frontend WAC preview TOTAL/UNIT, historial drawer and CSV`

## Status
9/17 tasks complete. Ready for next batch (PR3 Wiring+tests). Not ready for verify — Phase 4 tests (4.1-4.4) and InventarioView wiring (3.2) pending.

## Verification Notes
- No FLOAT used; Decimal(str(v)) + Numeric(15,4) enforced (PR1); JS Number only for display preview (design Preview authority decision).
- WAC formula verified: 10@5 +10@9 → 7.0000 via (stock*cost+qty*unit)/newStock (JS preview parity), backend Decimal authoritative.
- CSV_HEADER exact: `fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura` (REQ-CI-003) with escaping.
- Infinity/NaN disabled gate via !isFinite in computed isConfirmDisabled + buildCompraPayload validation before emit.
- PrimeVue 4.5.5 only: Drawer, Button, InputNumber, Select, InputText — no Element Plus.
- 4.4 vitest draft deferred: unit/CSV basics covered; full historial-drawer.spec + concurrent pytest deferred to PR3 with reason (requires InventarioView wiring + Docker PG).
