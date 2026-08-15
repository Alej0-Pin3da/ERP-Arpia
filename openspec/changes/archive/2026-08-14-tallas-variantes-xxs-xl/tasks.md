# Tasks: Tallas de variantes (XXS–XL)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~410–450 (backend prod ~130, backend tests ~185, frontend prod ~35, frontend tests ~95) |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 backend (T1–T6) → PR 2 frontend (T7–T10) |
| Delivery strategy | ask-on-risk (not provided at launch — resolve before apply) |

```
Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium
```

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend: F1 variants+Set Celeno+price, F5 omit+idempotency, F7 N7a/N7g | PR 1 | `python -m pytest backend/tests/test_migrate_catalog.py backend/tests/test_migrate_sales.py backend/tests/test_migrate_validate.py -q` | Real F1→F5→F7 commit run vs ARPIA.xlsx on Docker Postgres; re-run F5 to prove no-dup | Revert backend/migrate+backend/tests; delete Set Celeno + its 6 variants (no FK refs yet) |
| 2 | Frontend: ventas.ts hooks + VentasForm variant-required | PR 2 | `npm test -- --run` + `vue-tsc --noEmit` (frontend/) | Browser: register a sized sale without variant → blocked; with variant → emits | Revert frontend files only; backend 400 guard stays as safety net |

## Phase 1: Backend catalog (MIG-1, MIG-2) — TDD

- [x] **T1** (RED) `backend/tests/test_migrate_catalog.py` — plan from real xlsx: 5 sized products × 6 = 30 variantes; `conteo_productos == 14`; Set Celeno entry with `precio_venta_sugerido` 75000; `aplicar_plan` → DB price 75000 + re-apply keeps it; `upsert_producto` duplicate variantes → 6 rows; Corset Garras/combos → 0 rows. Existing `len(PRODUCTOS_CATALOGO)` asserts auto-adapt.
- [x] **T2** (GREEN) `backend/migrate/catalog.py` — D1: `variantes=("XXS","XS","S","M","L","XL")` on Set Aelo, Set Ocipete, Blusa Manga Larga, Blusa Manga Corta + new Set Celeno entry (tipo Set, `precio_venta_sugerido` 75000, 6 variantes); `ProductoPlan.precio_sugerido: Decimal | None = None` (frozen, default); `plan_catalogo` maps `precio_venta_sugerido`; `aplicar_plan` forwards it; `upsert_producto` refreshes price on existing product only when `precio_sugerido is not None`.

## Phase 2: Backend sales (MIG-3, MIG-4) — TDD

- [x] **T3** (RED) `backend/tests/test_migrate_sales.py` — mini row for sized product (variantes seeded) WITHOUT size: `aplicar_ventas` → `res["omitidas"] == 1`, other row inserted, 0 DetalleVenta for omitted, no `DomainValidationError`; NULL-matching: pre-inserted NULL-variant detail for a variant-resolving plan line → re-run `insertadas == 0`; combo (None) does not match a variant DB row.
- [x] **T4** (GREEN) `backend/migrate/sales.py` — D2/D3: `from sqlalchemy import or_`; exported `variante_coincide(plan, db)` (None→only None; set→exact+None); omit predicate inside step-1 loop (sales.py:457-473) after `variante_id` resolves: `variante_id is None and producto.variantes and not combo` → `res["omitidas"] += 1`, `report.warn(...)` (design MIG-3 message), `continue` (never reaches inventory.py:61-62 guard); `_contar_existentes` NULL-matching branch.

## Phase 3: Backend validate (MIG-5) — RED first, ONE commit (design WARNING)

- [x] **T5** (RED) `backend/tests/test_migrate_validate.py` — `_preparar_entorno` seeds FULL 14-product catalog (loop `upsert_producto` over `PRODUCTOS_CATALOGO`); cleanup removes the 14 canonical products BEFORE `_borrar_socios_y_tipos` (FK RESTRICT on Tipos); new tests: N7a pieza `"productos 14/14"`; N7g omitidas-no-duplicadas (sized size-less plan line kept in plan + NULL DB row → OK). Confirm RED vs current `_n7g_idempotencia`; if naive state passes "by luck", extend so a variant plan key must match a NULL DB row (exact-key `db_ventas.get` returns 0 there).
- [x] **T6** (GREEN) `backend/migrate/validate.py` — D4/D5: `_productos_del_plan` adds `{normalizar_nombre(p.nombre) for p in plan.catalogo.productos}` to BOM∪ventas; `_n7g_idempotencia` ventas section: normalize DB variant names, per-key compare via `variante_coincide`, keep omitted lines in `plan_ventas` (docstring D4 false-positive trap). **T5+T6 MUST be a single commit.**

## Phase 4: Frontend utils (VV-1..VV-4) — TDD

- [x] **T7** (RED) `frontend/tests/unit/ventas.spec.ts` — `requiereVariante`: null product → false, 0 variantes → false, ≥1 → true; `detallesSinVariante`: sized missing → returned, sized chosen → not, variant-less → not, null product → not.
- [x] **T8** (GREEN) `frontend/src/utils/ventas.ts` — D5: export `requiereVariante(row, variantes)` and `detallesSinVariante(detalles, variantesPorProducto)` exactly per design interface.

## Phase 5: Frontend form (VV-1..VV-4) + tests

- [x] **T9** (GREEN) `frontend/src/components/ventas/VentasForm.vue` — D5/D6: variant select `:disabled="variantesDe(row).length === 0"` (replace line-212 `row.producto_id === null`); `submit()` awaits cached in-flight `loadVariantesFor` (idempotent, closes race) then blocks with `ElMessage.warning` + NO emit when `detallesSinVariante(...)` non-empty; shared create/edit path.
- [x] **T10** `frontend/tests/component/ventas-form.spec.ts` — VV-1: sized no variant → warning + no emit; sized + variant → emit with `variante_id`; VV-2: variant-less → emit without; empty line select disabled; VV-3: combo → one detail no `variante_id`; edit mode: prefill sized-with-null blocked until variant chosen.

## Phase 6: Verification

- [x] Full backend suite `python -m pytest backend/tests -q` green (512 passed; 4 pre-existing test_migrate_stock.py failures verified identical on main — out of scope); frontend `npm test -- --run` green (498 passed) + `vue-tsc --noEmit` N/A (tool not installed; plain-tsc clean on touched pure-TS files); success criteria from proposal (14 productos, 30 variantes, F5 2 omitidas + no-dup re-run, VentasForm blocks) — all PASS per verify-report.md.