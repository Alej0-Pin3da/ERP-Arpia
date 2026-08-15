```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:7f510c2f439a143adacd9079b761c52f3d4e84954f68008c6d74999e3dbbe73e
verdict: pass
blockers: 0
critical_findings: 0
requirements: 9/9
scenarios: 17/17
test_command: backend\.venv\Scripts\python -m pytest backend/tests -q -k "not (alias_tira or alias_argollas or alias_varilla or exacto_primero)"
test_exit_code: 0
test_output_hash: sha256:283933981ba68e1517bece3afe28645a646e1e843ce40a6ba495d514e39d3ec9
build_command: npm run build
build_exit_code: 0
build_output_hash: sha256:e22c443feadc769fbb97d81677d6f01c8008de2feacf088fadb89809fb8f6e61
```

## Verification Report

**Change**: tallas-variantes-xxs-xl
**Version**: N/A (delta specs, no version field)
**Mode**: Strict TDD (config `strict_tdd: true`; runner present)

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 10 (T1–T10) + Phase-6 verification task (this report) |
| Tasks complete | 10/10 implementation |
| Tasks incomplete | 0 (Phase-6 was the only pending item; proven by this report) |

### Build & Tests Execution

**Build**: ✅ Passed — `npm run build` (frontend/) exit 0, built in 9.23s; only non-blocking chunk-size warning (>500 kB index chunk, pre-existing).
```text
✓ built in 9.23s
(!) Some chunks are larger than 500 kB after minification. (informational)
```

**Tests — backend (change-relevant gate)**: ✅ 512 passed, 4 deselected, exit 0
```text
backend\.venv\Scripts\python -m pytest backend/tests -q -k "not (alias_tira or alias_argollas or alias_varilla or exacto_primero)"
512 passed, 4 deselected, 9 warnings in 66.95s
```
**Tests — backend (full suite, unfiltered)**: 512 passed, **4 failed**, exit 1. The 4 failures are `test_migrate_stock.py` alias-resolution tests. **Verified pre-existing**: checked out `408aeaf` (main, the change base) and ran `backend/tests/test_migrate_stock.py` — the SAME 4 tests fail there with the same assertion (`assert res["seteados"] == 1` → `assert 0 == 1`), `4 failed, 10 passed`. They are NOT regressions of this change and are documented out-of-scope (proposal success criterion 5 explicitly qualifies "pytest green" with these known failures).

**Tests — frontend**: ✅ 55 files, 498 passed (498), exit 0 — `npm test -- --run` from frontend/. Matches the slice-2 apply report (498).

**Lint**: ✅ `ruff check backend` → "All checks passed!" exit 0. ✅ `npm run lint` (eslint) → clean, exit 0 (supplementary).

**Type check**: ⚠️ vue-tsc NOT installed and NOT declared (verified: absent from package.json devDependencies, no `vue-tsc` npm script, no `node_modules/.bin/vue-tsc`). Per the verify contract, tool-unavailable is reported — NOT gated and NOT fabricated. Best-effort strict `tsc --noEmit` (typescript 5.7.3 present) on the two pure-TS touched files (`src/utils/ventas.ts`, `tests/unit/ventas.spec.ts`) → exit 0, 0 errors. The `.vue`-touching files (`VentasForm.vue`, `ventas-form.spec.ts`) cannot be type-checked without vue-tsc; they are covered by the 498-test vitest run (runtime) and clean eslint.

**Coverage**: ➖ Not available — `pytest-cov` not installed; `@vitest/coverage-v8` not installed. Reported per Strict-TDD module as informational, not blocking.

### Spec Compliance Matrix

Requirements counted from the two delta specs: migracion-catalogos (MIG-1..MIG-5, 10 scenarios) + ventas-variantes (VV-1..VV-4, 7 scenarios) = **9 requirements / 17 scenarios**.

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| MIG-1 Variant seeding via PRODUCTOS_CATALOGO tuples | Seeds 30 variants across the five sized products (precio_venta NULL) | `test_migrate_catalog.py::test_plan_catalogo_real_30_variantes_y_14_productos` (REAL xlsx, asserts 5×6=30, `conteo_productos==14`) + `test_aplicar_plan_set_celeno_precio_y_reapply` (persists 6 variants); NULL price: model `VarianteProducto.precio_venta nullable=True`, upsert creates variants without price | ✅ COMPLIANT |
| MIG-1 | Re-run does not duplicate variants | `test_migrate_catalog.py::test_upsert_producto_variantes_duplicadas_6_filas` (upsert twice → 6 rows, same id) | ✅ COMPLIANT |
| MIG-1 | Non-sized products get no variant rows | `test_migrate_catalog.py::test_plan_catalogo_real_sin_variantes_en_corset_garras_y_combos` (REAL xlsx; Corset Garras + combos → `variantes == ()`) | ✅ COMPLIANT |
| MIG-2 Set Celeno catalog entry | Set Celeno created at the locked price (75000, count 14) | `test_plan_catalogo_real_30_variantes_y_14_productos` (REAL xlsx: `conteo_productos == 14`, `celeno.precio_sugerido == Decimal("75000")`) + `test_aplicar_plan_set_celeno_precio_y_reapply` (DB `precio_venta_sugerido == 75000`, re-apply stable, 6 variants) | ✅ COMPLIANT |
| MIG-2 | Workbook 65000 is not used | Code comment in `PRODUCTOS_CATALOGO` documents the locked 75000 decision (65000 = discount/mis-entry); persisted price asserted 75000 by the tests above; `aplicar_plan` reports the price to the F1 report | ✅ COMPLIANT |
| MIG-3 F5 omits and reports size-less rows | The two size-less rows are omitted and the phase completes | `test_migrate_sales.py::test_aplicar_ventas_omitida_sin_talla_no_estalla` (mini row sized-product-without-size: `res["omitidas"] == 1`, `insertadas == 1` for the variant-less product, no `DomainValidationError`); real-row identification is generic by predicate (no hardcoding); report entry: `report.warn(...)` carries product name, date, qty, reason (code-verified) | ✅ COMPLIANT |
| MIG-3 | No default variant is invented | Same test: 0 `DetalleVenta` rows for the omitted product; omit `continue` fires before any insert/explosion | ✅ COMPLIANT |
| MIG-4 F5 NULL-matching idempotency | Re-run after seeding does not duplicate the 21 sales | `test_migrate_sales.py::test_aplicar_ventas_rerun_matchea_fila_null_historica` (pre-inserted NULL-variant detail matched by variant-resolving plan line → no dup) | ✅ COMPLIANT |
| MIG-4 | NULL plan line still matches NULL DB row | `test_migrate_sales.py::test_aplicar_ventas_combo_sin_variante_no_matchea_fila_con_variante` + combo-never-omitted guard (`test_aplicar_ventas_omitida_sin_talla_no_estalla` asserts combos `omitidas == 0`) | ✅ COMPLIANT |
| MIG-5 N7 validation aware of omissions and NULL-matching | Validation passes after the migrated state (14 productos, 30 variants, 19 sales, 2 omitted) | `test_migrate_validate.py::test_n7a_productos_14_de_14` (N7a "productos 14/14" OK) + `test_n7g_variante_null_matching_detecta_duplicado` + `test_n7g_omitida_sin_talla_no_duplicada` (omitted lines stay in plan, no false duplicate) | ✅ COMPLIANT |
| VV-1 Variant required for sized products | Sized product without variant is blocked | `ventas-form.spec.ts` 'VV-1: blocks a sized product without a variant and emits nothing' (warning text asserted, `emitted('submit')` undefined) + unit `requiereVariante` ≥1 → true + edit-mode 'VV-1: edit prefill with a sized product and null variant is blocked until a variant is chosen' | ✅ COMPLIANT |
| VV-1 | Sized product with variant submits | `ventas-form.spec.ts` 'VV-1: emits with variante_id once a variant is chosen' (payload `variante_id: 5`) | ✅ COMPLIANT |
| VV-2 Select hidden or disabled without variants | Variant-less product does not require a variant | `ventas-form.spec.ts` 'VV-2: a variant-less product submits without a variante' (payload omits `variante_id`) | ✅ COMPLIANT |
| VV-2 | Empty line select is disabled | `ventas-form.spec.ts` 'VV-2: the variant select is disabled on an empty line' + code `:disabled="variantesDe(row).length === 0"` | ✅ COMPLIANT |
| VV-3 Combos remain single-line NULL-variant | Combo sale needs no variant | `ventas-form.spec.ts` 'VV-3: a combo sale submits one detail without a variante' (one detail, no `variante_id`) | ✅ COMPLIANT |
| VV-4 Lazy variant loading drives the requirement | Loaded variants populate the select (6 sizes, required) | `ventas-form.spec.ts` 'VV-4: a sized product enables the select once its variants load' + `loadVariantesFor` in-flight cache code (D6) | ✅ COMPLIANT |
| VV-4 | Empty list disables the requirement | `ventas-form.spec.ts` 'VV-4: the select stays disabled when the loaded variant list is empty' + unit `detallesSinVariante`/`requiereVariante` empty-list cases | ✅ COMPLIANT |

**Compliance summary**: 17/17 scenarios compliant (each with a passing covering test at runtime).

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| MIG-1 seeding | ✅ Implemented | `PRODUCTOS_CATALOGO` `variantes` tuples on the 5 sized products; `upsert_producto` dedups by `(producto_id, nombre_variante)`; no phantom NULL row for non-sized products |
| MIG-2 Set Celeno | ✅ Implemented | Entry `{"nombre":"Set Celeno","tipo":"Set","precio_venta_sugerido":75000,"variantes":6}`; count 13→14 |
| MIG-3 omit+report | ✅ Implemented | Predicate in step-1 resolution loop (before `esperadas`/`resueltas` and the `inventory.py` guard); `report.warn` with product/date/qty/reason; combos excluded explicitly |
| MIG-4 NULL-matching | ✅ Implemented | `variante_coincide(plan, db)` exported (None→only None; set→exact+None); `_contar_existentes` `or_` branch |
| MIG-5 N7 mirroring | ✅ Implemented | `_productos_del_plan` includes full catalog (D5); `_n7g_idempotencia` normalizes DB variant names, per-key `variante_coincide`, omitted lines kept in plan (D4, docstring explains the false-positive trap) |
| VV-1..VV-4 | ✅ Implemented | `requiereVariante`/`detallesSinVariante` exported; `submit()` awaits in-flight loads then blocks with `ElMessage.warning` + no emit; select disabled when `variantesDe(row).length === 0`; shared create/edit path |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| D1 Price plumbing (`precio_sugerido` on `ProductoPlan`; refresh only when not None) | ✅ Yes | `test_upsert_producto_refresca_precio_solo_cuando_no_none` proves the only-when-not-None rule |
| D2 Omit predicate in step-1 loop, combo-excluded | ✅ Yes | Code matches design snippet verbatim (omit → `res["omitidas"]`, warn, `continue`) |
| D3 `_contar_existentes` NULL-matching + exported `variante_coincide` | ✅ Yes | `or_(== variant_id, is_(None))` branch; shared with N7g |
| D4 N7g: normalize DB names, `variante_coincide`, keep omitted lines in plan | ✅ Yes | Docstring carries the D4 rationale; latent raw-vs-normalized bug fixed |
| D5 N7a `_productos_del_plan` includes catalog products | ✅ Yes | `{normalizar_nombre(p.nombre) for p in plan.catalogo.productos}` union |
| D6 Frontend helpers + await-loads-then-block | ✅ Yes | Helper signatures match the design interface exactly; in-flight promise cache closes the submit-before-load race |

No design deviations found. (Notable: apply additionally fixed a pre-existing broken named-type import in VentasForm.vue — type-only, runtime-neutral, documented in apply-progress as a deviation from nothing; it does not change behavior.)

### TDD Compliance (Strict TDD)
| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | apply-progress (engram #502) contains RED/GREEN tables per task; tasks.md marks RED→GREEN for T1–T6 |
| All tasks have tests | ✅ | 10/10 — T1/T3/T5/T7/T10 RED legs have test files; T2/T4/T6/T8/T9 are GREEN legs on those same files |
| RED confirmed (tests exist) | ✅ | Test files verified on disk: test_migrate_catalog.py, test_migrate_sales.py, test_migrate_validate.py, ventas.spec.ts, ventas-form.spec.ts |
| GREEN confirmed (tests pass) | ✅ | Re-executed: backend gate 512 passed (4 pre-existing deselected), frontend 498 passed |
| Triangulation adequate | ✅ | Multi-case per behavior (3 MIG-1 tests, 4 upsert/price tests, 8 component VV tests incl. edit mode, 2 N7g tests) |
| Safety Net for modified files | ⚠️ | Slice-2 documented (pre-existing `es_regalo` test updated, existing suite run); slice-1 (T1–T6) safety-net not explicitly recorded in apply-progress |

**TDD Compliance**: 5/6 checks passed (1 partial ⚠️ on slice-1 safety-net documentation; informational).

Note: apply-progress states "Standard mode (no strict TDD active per orchestrator)" while `openspec/config.yaml` sets `strict_tdd: true`. This verify ran under Strict TDD per config; the discrepancy is reported for the orchestrator, and the actual RED→GREEN evidence is present regardless.

### Test Layer Distribution
| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit (pure functions) | 7 new (requiereVariante ×3, detallesSinVariante ×4) | tests/unit/ventas.spec.ts | vitest |
| Integration (DB + real xlsx) | ~15 new across catalog/sales/validate | test_migrate_catalog.py, test_migrate_sales.py, test_migrate_validate.py | pytest + real PostgreSQL (Docker) + ARPIA.xlsx |
| Component (jsdom + Element Plus) | 8 new + 1 updated | tests/component/ventas-form.spec.ts | vitest + @vue/test-utils |
| E2E | 0 | — | not installed |
| **Total** | **~30 new/updated + full-suite re-run** | **5 files** | |

### Changed File Coverage
Coverage analysis skipped — no coverage tool detected (`pytest-cov` and `@vitest/coverage-v8` not installed). Informational per Strict-TDD module; not a failure.

### Assertion Quality
Audit of the 5 changed test files (Step 5f): no tautologies, no ghost loops, no orphan empty-asserts (every `toEqual([])`/`toBe(false)` has a non-empty/true companion in the same describe), no type-only assertions used alone (the two `expect(emitted).toBeDefined()` are followed by `toMatchObject` payload assertions), no smoke-only tests, no implementation-detail coupling. All assertions verify real behavior with varied expected values.

**Assertion quality**: ✅ All assertions verify real behavior (0 CRITICAL, 0 WARNING).

### Quality Metrics
**Linter**: ✅ No errors — `ruff check backend` clean; `npm run lint` clean.
**Type Checker**: ⚠️ Partial — strict `tsc --noEmit` clean on the 2 pure-TS touched files; `vue-tsc` not installed → the 2 `.vue`-touching files not machine type-checked (tool-unavailable, not gating). The 119 pre-existing vue-tsc error count from the apply report could not be independently re-verified without the tool; the claim "repo does not declare vue-tsc" is directly verified (absent from package.json, lockfile, scripts, node_modules).

### Success Criteria (from proposal)
| Criterion | Result | Evidence |
|-----------|--------|----------|
| F1 seeds 30 variants across 5 sized products, `precio_venta` NULL | ✅ PASS | REAL-xlsx test: 5×6=30 variants; `VarianteProducto.precio_venta nullable=True`, upsert never sets it → NULL |
| Set Celeno in catalog @75000; `conteo_productos == 14` | ✅ PASS | `test_plan_catalogo_real_30_variantes_y_14_productos` (both asserts) + DB persistence/re-apply test |
| F5 completes: 2 rows omitted + reported, no DomainValidationError, re-run no duplicates | ✅ PASS | `test_aplicar_ventas_omitida_sin_talla_no_estalla` (omitidas==1, no explosion, 0 inserts for omitted) + `test_aplicar_ventas_rerun_matchea_fila_null_historica` (0 dups on re-run); the real 2 rows match the predicate generically; report.warn carries product/date/qty/reason |
| VentasForm requires variant on sized products; combos single-line NULL-variant | ✅ PASS | Component tests VV-1 block/emit, VV-2 variant-less, VV-3 combo, edit mode |
| `pytest backend/tests -q` green (with the known 4 pre-existing stock failures documented) | ✅ PASS | Full suite 512 passed + 4 pre-existing stock failures verified IDENTICAL on main (408aeaf); change-relevant gate 512 passed / 4 deselected / exit 0 |

### Issues Found
**CRITICAL**: None.
**WARNING**:
1. 4 pre-existing `test_migrate_stock.py` alias-resolution failures (out of scope, verified identical on main `408aeaf`; full-suite exit code is 1). The proposal's "pytest green" criterion is met only modulo these documented failures.
2. `vue-tsc` is not installed/declared — the 2 `.vue`-touching files' type-cleanliness is not machine-verified (tool-unavailable). Plain-tsc strict check passed on the pure-TS touched files; eslint clean; 498 vitest tests pass.
3. Strict-TDD mode discrepancy: config `strict_tdd: true` vs apply-progress "Standard mode" — informational, RED→GREEN evidence is present either way.
**SUGGESTION**:
1. Add `vue-tsc` to devDependencies + a `typecheck` script, then fix the ~119 pre-existing type errors in a separate change (repo-wide gate).
2. No test asserts the MIG-3 `report.warn` entry text verbatim (covered by code inspection only); a small report-content assertion would lock the report contract.
3. `--deselect` is non-functional in this environment (pytest 8.3.4 + Windows node-ID matching); the change-relevant gate uses `-k` filters instead — documented here for future verifies.
4. Slice-1 (T1–T6) safety-net documentation missing from apply-progress.

### Verdict
**PASS** — all 9 requirements / 17 scenarios have passing covering tests; design decisions D1–D6 followed; success criteria pass; only known pre-existing conditions remain (4 stock failures identical on main, vue-tsc unavailable). No regressions introduced by this change.