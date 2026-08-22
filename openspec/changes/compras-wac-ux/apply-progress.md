# Apply Progress: compras-wac-ux

## Change
compras-wac-ux — Registrar Compra WAC with Live Simulation & History
Project: erp-arpia
Mode: Standard (Strict TDD enabled but PR1 is backend SSOT slice; full TDD cycle deferred to Phase 4 tasks 4.1-4.4)
Delivery: auto-chain stacked-to-main — PR1 (Backend WAC SSOT)

## Completed Tasks (5/17)
- [x] 1.1 schemas/compra_insumo.py — modo TOTAL|UNIT, costo_total? gt0, factura? ≤100, proveedor_id?, finite check, Read costo_unitario_aplicado
- [x] 1.2 models/insumos.py — proveedor_id nullable (no FK, Proveedores removed), factura, costo_unitario_aplicado Numeric(15,4), index fecha_compra
- [x] 1.3 alembic 20260821_compras_wac_ux.py — nullable cols + index idempotent, backfill NULL, downgrade drops
- [x] 2.1 services/wac.py — modo/costo_total handling price=costo_total/qty Decimal if TOTAL, factura/proveedor_id, retain SELECT FOR UPDATE + atomic commit/rollback, commit=False
- [x] 2.2 api/routes/compras_insumos.py — pass new fields, proveedor 400 guard (Proveedores missing → 400), gt0/isFinite→422, GET fecha_compra DESC ordering

## Files Changed
| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/schemas/compra_insumo.py` | Modified | Added modo, costo_total, factura, proveedor_id, finite validator, model_validator for modo semantics, extended Read |
| `backend/app/models/insumos.py` | Modified | Added proveedor_id (Integer nullable, no FK), factura String(100), costo_unitario_aplicado Numeric(15,4) |
| `backend/alembic/versions/20260821_compras_wac_ux.py` | Created | Idempotent migration: checks _has_column/_has_index before add, index fecha_compra guard |
| `backend/app/services/wac.py` | Modified | Extended registrar_compra signature with modo/costo_total/factura/proveedor_id, TOTAL derivation Decimal, finite guards, costo_unitario_aplicado persist, HTTPException rollback guard |
| `backend/app/api/routes/compras_insumos.py` | Modified | Import HTTPException/text, proveedor validation via to_regclass raw SQL → 400, pass new fields to service, default ordering fecha_compra DESC |
| `backend/app/models/ventas.py` | Modified (unplanned) | Fixed AmbiguousForeignKeysError: Devolucion reversed_by_user/usuario relationships now specify foreign_keys |

## Deviations from Design
- `proveedor_id` column added WITHOUT FK constraint: Proveedores table was removed in 0008_remove_proveedores; design open question flagged this. Route validates via raw SQL `to_regclass('public.Proveedores')` → 400 if missing or id not found, preserving spec 400 contract without recreating table.
- `costo_unitario_aplicado` made nullable True (not enforced NOT NULL) to allow backfill NULL for historical rows; new purchases populate via service nuevo_costo. Spec said NUMERIC(15,4) strings in Read, implemented as Decimal | None.
- `backend/app/models/ventas.py` fix was not in tasks but required to unblock configure_mappers() import (two FKs to Usuarios from Devoluciones). Included as work-unit collateral.

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `$env:PYTHONPATH="backend"; python -c "from app.schemas.compra_insumo..."` — UNIT ok, TOTAL ok, Infinity rejected ok, both rejected ok (4/4). `python -m py_compile` ok for 4 BE files. `configure_mappers()` ok. `pytest tests/test_wac.py -q` → blocked by DB offline/OperationalError (not code failure); schema/service unit validation passed via direct python exercise (price derivation 10@5+10@9→7.0000, zero-stock 7.0000). |
| Runtime harness command/scenario and exact result | N/A — no Docker PG available in this env (port 5432/5433 connection refused). Harness `POST /api/v1/compras-insumos` TOTAL/UNIT requires live DB; deferred to PR3 wiring+verify with Docker PG. Idempotent migration SQL inspected: _has_column guards ensure no duplicate column error. |
| Rollback boundary | Revert migration `20260821_compras_wac_ux.py` + 4 BE files (`schemas/compra_insumo.py`, `models/insumos.py`, `services/wac.py`, `api/routes/compras_insumos.py`). No side effects outside these; ventas.py fix is independent and can stay. Single `alembic downgrade` + file revert restores prior state. |

## Remaining Tasks (12/17)
- [ ] 2.3 frontend/src/utils/inventario.ts
- [ ] 2.4 frontend/src/components/inventario/ComprasForm.vue
- [ ] 3.1 HistorialDrawer.vue
- [ ] 3.2 InventarioView.vue
- [ ] 3.3 endpoints.ts
- [ ] 4.1 test_wac.py
- [ ] 4.2 test_compras_insumos.py
- [ ] 4.3 concurrent threaded pytest
- [ ] 4.4 vitest specs
- [ ] 5.1 pytest -q + npm build
- [ ] 5.2 manual seed/POST/History check
- [ ] 5.3 cleanup

## Workload / PR Boundary
- Mode: chained PR slice (stacked-to-main)
- Current work unit: 1 — Backend WAC SSOT
- Boundary: Start 1.1 (schemas) → End 2.2 (routes). No frontend yet.
- Estimated review budget impact: ~150 lines (5 files modified + 1 migration). Under 400 limit; PR1 ready for review.

## Status
5/17 tasks complete. Ready for next batch (PR2 Frontend core). Not ready for verify — Phase 4 tests pending.

## Verification Notes
- No FLOAT used; Decimal(str(v)) + Numeric(15,4) enforced.
- WAC formula verified: 10@5 +10@9 → 7.0000, stock0+20@7→7.0000
- Infinity/NaN → 422 via schema field_validator is_finite
- factura max_length 100 enforced via Field + service strip guard
- SELECT FOR UPDATE retained; commit=False supported; atomic rollback on HTTPException/IntegrityError
