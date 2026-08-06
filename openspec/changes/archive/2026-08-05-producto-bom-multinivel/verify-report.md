```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:89b33873d49efb3ceed7bde746e415de37410695d84a454ca755c96336788bf8
verdict: pass
blockers: 0
critical_findings: 0
requirements: 14/14
scenarios: 44/44
test_command: python -m pytest backend/tests -q
test_exit_code: 0
test_output_hash: sha256:89b33873d49efb3ceed7bde746e415de37410695d84a454ca755c96336788bf8
build_command: python -c "from app.main import app; print('BUILD_OK')"
build_exit_code: 0
build_output_hash: sha256:3685c52795327d9438693196069984eccff35ef9aff3cd44e9fbe97331311c11
```

## Verification Report

**Change**: producto-bom-multinivel
**Version**: N/A (delta specs at HEAD of the current branch)
**Mode**: Strict TDD (full artifacts: proposal + specs + design + tasks + apply-progress)
**Run ledger token**: `sha256:49874f6a7a31e0bb951c851d2170875662186c266dd66e45b59ff80485deeabd` (request req-s3-v-acquire-001)
**Branch**: feat/phase3-costos-slice3 @ 555e7a7 (stacked: slice1 34ba8b1 → slice2 2b28cc2 → slice3 555e7a7)

### Completeness
| Metric | Value |
|--------|-------|
| Implementation tasks total (1.1–3.7) | 24 |
| Implementation tasks complete | 24 |
| Implementation tasks incomplete | 0 |
| Verify-phase tasks (4.1–4.2) | 2 — both executed and passed by THIS verification |
| Test files (change-specific) | 3 (`test_productos.py`, `test_bom.py`, `test_costos.py`) |

Note: apply-progress states "25/25" for slices 1–3, but the authoritative tasks artifact contains 24 implementation tasks (9 + 8 + 7). Counts in this report follow the tasks artifact.

### Build & Tests Execution
**Build (app import / router wiring)**: ✅ Passed, exit 0
```text
python -c "from app.main import app; print('BUILD_OK')" → BUILD_OK (exit 0)
Route probe: /productos/{producto_id}/costo live, 8 BOM routes, 4 variantes routes, 59 total API routes
```

**Tests (full suite)**: ✅ 122 passed / 0 failed / 0 skipped, exit 0 (19.79s)
```text
python -m pytest backend/tests -q → 122 passed in 19.79s
```

**Tests (change-specific)**: ✅ 69 passed / 0 failed (24 productos + 27 bom + 18 costos), exit 0

**Coverage**: ➖ Not available — pytest-cov/coverage not installed in backend/.venv.

**Post-suite DB state**: 0 leftover rows in BOM_Insumos, BOM_Productos, Variantes_Producto, Productos, Tipos_Producto (cleanup helpers verified working).

### Spec Compliance Matrix
Authoritative counts from the three delta specs: productos 4 reqs / 15 scenarios, bom 5 reqs / 14 scenarios, costos-produccion 5 reqs / 15 scenarios → 14 reqs / 44 scenarios.

#### productos (4 reqs / 15 scenarios)
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Tipo_Producto CRUD | Create a type | `test_create_tipo_admin_returns_201` | ✅ COMPLIANT |
| Tipo_Producto CRUD | Duplicate type name | `test_create_tipo_duplicate_name_returns_409` | ✅ COMPLIANT |
| Tipo_Producto CRUD | Read missing type | `test_get_tipo_missing_returns_404` | ✅ COMPLIANT |
| Tipo_Producto CRUD | Paginated listing | `test_list_tipos_paginated_limit_offset_order_by_id` | ✅ COMPLIANT |
| Producto CRUD | Create a product | `test_create_producto_admin_returns_201_with_defaults` | ✅ COMPLIANT |
| Producto CRUD | Invalid type reference | `test_create_producto_invalid_tipo_returns_400` | ✅ COMPLIANT |
| Producto CRUD | Negative fixed cost | `test_create_producto_negative_costos_returns_422` | ✅ COMPLIANT |
| Producto CRUD | Read missing product | `test_get_producto_missing_returns_404` | ✅ COMPLIANT |
| Variante_Producto CRUD | Create a variant | `test_create_variante_returns_201` | ✅ COMPLIANT |
| Variante_Producto CRUD | Duplicate variant name | `test_create_variante_duplicate_name_returns_409` | ✅ COMPLIANT |
| Variante_Producto CRUD | Variants of missing product | `test_list_variantes_missing_product_returns_404` | ✅ COMPLIANT |
| Variante_Producto CRUD | Delete missing variant | `test_delete_variante_missing_returns_404` | ✅ COMPLIANT |
| Authorization | Unauthenticated mutation | `test_create_producto_requires_auth` (+tipo, +variante) | ✅ COMPLIANT |
| Authorization | Operador forbidden mutation | `test_delete_producto_operador_forbidden` | ✅ COMPLIANT |
| Authorization | Any role reads | `test_get_productos_consulta_allowed` | ✅ COMPLIANT |

#### bom (5 reqs / 14 scenarios)
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| BOM_Insumos CRUD | Create an insumo line | `test_create_bom_insumo_returns_201_with_waste_default_0` | ✅ COMPLIANT |
| BOM_Insumos CRUD | Nonexistent insumo | `test_create_bom_insumo_insumo_missing_returns_400` | ✅ COMPLIANT |
| BOM_Insumos CRUD | Waste out of range | `test_create_bom_insumo_waste_out_of_range_returns_422` | ✅ COMPLIANT |
| BOM_Insumos CRUD | Variant of another product | `test_create_bom_insumo_variante_de_otro_producto_returns_400` | ✅ COMPLIANT |
| BOM_Insumos CRUD | Nonexistent parent product | `test_list_bom_insumos_parent_missing_returns_404` | ✅ COMPLIANT |
| Duplicate insumo-line rule | Duplicate NULL-variant row | `test_validar_linea_null_null_es_409` + `test_create_bom_insumo_dup_null_returns_409` | ✅ COMPLIANT |
| Duplicate insumo-line rule | Duplicate variant-specific row | `test_validar_linea_misma_variante_es_409` + `test_create_bom_insumo_dup_variant_returns_409` | ✅ COMPLIANT |
| Duplicate insumo-line rule | NULL rule and variant rule coexist | `test_validar_linea_null_y_variante_ok` + `test_create_bom_insumo_null_y_variante_returns_201` | ✅ COMPLIANT |
| Variante semantics | Base rule applies to all variants | `test_costo_variante_sin_reglas_cae_a_base` | ✅ COMPLIANT |
| Variante semantics | Variant-specific override | `test_costo_variante_override_no_se_suma_base` | ✅ COMPLIANT |
| Waste semantics | Effective quantity with waste | `test_costo_desperdicio_en_contribucion_insumo` | ✅ COMPLIANT |
| BOM_Productos CRUD | Create a combo line | `test_create_bom_producto_returns_201` | ✅ COMPLIANT |
| BOM_Productos CRUD | Duplicate combo line | `test_create_bom_producto_dup_returns_409` | ✅ COMPLIANT |
| BOM_Productos CRUD | Nonexistent included product | `test_create_bom_producto_included_missing_returns_400` | ✅ COMPLIANT |

#### costos-produccion (5 reqs / 15 scenarios)
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Recursive memoized cost service | Single-level insumo cost | `test_costo_single_level_insumos` (20.0000) | ✅ COMPLIANT |
| Recursive memoized cost service | Waste included in insumo contribution | `test_costo_desperdicio_en_contribucion_insumo` (60.0000) | ✅ COMPLIANT |
| Recursive memoized cost service | Multilevel combo cost | `test_costo_multinivel_combo` (70.0000) | ✅ COMPLIANT |
| Recursive memoized cost service | Shared subproduct computed once | `test_costo_diamante_subproducto_compartido_una_vez` (SQL count == 1) | ✅ COMPLIANT |
| Recursive memoized cost service | Variant override used in cost | `test_costo_variante_override_no_se_suma_base` | ✅ COMPLIANT |
| Recursive memoized cost service | Base rule fallback | `test_costo_variante_sin_reglas_cae_a_base` | ✅ COMPLIANT |
| Cycle detection | Direct cycle | `test_costo_ciclo_directo_409` | ✅ COMPLIANT |
| Non-fabricated or no-BOM rule | Non-fabricated product | `test_costo_no_fabricado_ignora_bom` (15.0000 + single fijos line) | ✅ COMPLIANT |
| Non-fabricated or no-BOM rule | Fabricated product without BOM | `test_costo_fabricado_sin_bom_solo_fijos` (15.0000 + single fijos line) | ✅ COMPLIANT |
| Cost endpoint | Endpoint returns total and breakdown | `test_get_costo_returns_total_y_desglose` | ✅ COMPLIANT |
| Cost endpoint | Missing product | `test_get_costo_missing_returns_404` | ✅ COMPLIANT |
| Cost endpoint | Cycle via endpoint | `test_get_costo_ciclo_returns_409` | ✅ COMPLIANT |
| Cost endpoint | Any authenticated role may read | `test_get_costo_consulta_allowed` (+401 `test_get_costo_requires_auth`) | ✅ COMPLIANT |
| Read-only Phase 4 contract | Callable inside a locked transaction | Code inspection + indirect runtime: `services/costos.py` contains zero `with_for_update`/`commit`/`rollback` statements — the engine is structurally read-only (only `db.get`/`db.scalars`); all 12 service tests execute the engine inside live sessions with no commit behavior. See SUGGESTION-1 for a regression test. | ✅ COMPLIANT |
| Read-only Phase 4 contract | Precision preserved in engine | `test_costo_precision_sin_redondeo` (66.66665 != 66.6667) | ✅ COMPLIANT |

**Compliance summary**: 44/44 scenarios COMPLIANT, 0 PARTIAL, 0 UNTESTED, 0 FAILING.

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| Tipo_Producto CRUD | ✅ Implemented | routes/tipos_productos.py; pagination order-by-id; 404/409; GET audited, mutations admin |
| Producto CRUD | ✅ Implemented | routes/productos.py; tipo FK→400; defaults applied; 422 via pydantic ge=0; 404 |
| Variante_Producto nested CRUD | ✅ Implemented | routes/productos.py nested; dup nombre per product 409 (DB unique + IntegrityError mapping) |
| Authorization | ✅ Implemented | deps.py require_roles/require_admin; 401 no token, 403 wrong role, GET any authenticated role |
| BOM_Insumos nested CRUD | ✅ Implemented | routes/bom.py; FK 400; waste 0–100 (422); same-product variant check (400) |
| Duplicate insumo-line rule | ✅ Implemented | `validar_linea_insumo_unica` explicit SELECT incl. `variante_id IS NULL` → 409; IntegrityError fallback; used on create+update |
| Variante semantics | ✅ Implemented | `_lineas_insumo_efectivas` — variant row overrides base per insumo; base kept for non-overridden insumos |
| Waste semantics | ✅ Implemented | effective qty = cantidad × (1 + pct/100); applied only to BOM_Insumos |
| BOM_Productos nested CRUD | ✅ Implemented | routes/bom.py; dup (combo, incluido) 409 via explicit SELECT + unique constraint |
| Recursive memoized cost service | ✅ Implemented | services/costos.py `_calcular`; memo keyed (pid, vid) intra-call; fijos added per level; Decimal arithmetic |
| Cycle detection | ✅ Implemented | path stack on producto_id → HTTPException 409 with cycle chain detail; cost-time only |
| Non-fabricated or no-BOM rule | ✅ Implemented | both branches return costos_operativos_fijos with single `operativos_fijos` line |
| Cost endpoint | ✅ Implemented | routes/costos.py GET /productos/{id}/costo (audited_user); 404/409; variante_id query param extension |
| Read-only Phase 4 contract | ✅ Implemented | no locks/commits in engine; read-only SELECTs only; callable inside any open transaction |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| 1 Slice order productos → bom → costos | ✅ Yes | 3 stacked commits, PR chain boundaries clean |
| 2 Engine in services/costos.py, pure reads | ✅ Yes | |
| 3 Signature `calcular_costo_produccion(db, producto_id, variante_id=None) -> Decimal`, no locks/commits | ✅ Yes | |
| 4 One core `_calcular` with root-only line collector | ✅ Yes | `lineas_out` passed only at root; children omit it |
| 5 Memoization intra-call keyed (pid, vid) | ✅ Yes | fresh `memo={}` per public call |
| 6 Cycle via path stack → 409, cost-time only | ✅ Yes | no write-time DFS |
| 7 Variante propagates to combo children; unknown vid falls back to NULL base | ✅ Yes | child called with same vid; `_lineas_insumo_efectivas` fallback |
| 8 Duplicate NULL-variant validator in routes/bom.py (explicit SELECT → 409) | ✅ Yes | module-level `validar_linea_insumo_unica` |
| 9 Root returns {total, lineas[]}; combo lines carry full recursive cost | ✅ Yes | proven by test asserting costo_unitario 30 / costo_total 60 |
| 10 Non-fabricated / no-BOM → fijos single line | ✅ Yes | |
| 11 Error mapping 401/403/404/400/422/409 | ✅ Yes | all covered by tests |
| 12 Duplicate nombre → IntegrityError → rollback → 409 | ✅ Yes | tipos & variantes; productos branch is defensive (no unique on nombre) — see SUGGESTION-2 |

### Invariants (task-level checks)
1. **Authz**: ✅ GET endpoints use `audited_user = require_roles("admin","operador","consulta")` on all three routers + tipos_productos + costos; all POST/PUT/DELETE use `require_admin`. 401 (no token) / 403 (operador) verified by tests.
2. **BOM duplicate NULL-variant → 409**: ✅ explicit SELECT validator (closes Postgres `NULL != NULL` hole) + IntegrityError fallback; tested at service and endpoint level.
3. **Cost engine**: ✅ cycle → 409 (path stack); `requiere_fabricacion=False` or no-BOM → `costos_operativos_fijos` (single line); memoization intra-call only, keyed `(producto_id, variante_id)`; Decimal arithmetic with no engine rounding (66.66665).
4. **Nested routes**: ✅ `/productos/{id}/variantes` (4 routes), `/productos/{id}/bom/insumos` (4), `/productos/{id}/bom/productos` (4), `/productos/{id}/costo` (1) — all live, no path collisions (verified via app import probe).

### TDD Compliance
| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | Found in apply-progress (slice-3 table; slices 1–2 in prior observations) |
| All tasks have tests | ✅ | 3/3 test files exist |
| RED confirmed (tests exist) | ✅ | 3/3 test files reference production code; slice-3 RED = ModuleNotFoundError collection error |
| GREEN confirmed (tests pass) | ✅ | 69/69 change tests + 122/122 full suite pass on execution |
| Triangulation adequate | ✅ | costos 10 service cases + 6 endpoint cases; validators 3 cases; no multi-scenario behavior with a single test |
| Safety Net for modified files | ✅ | 104/104 recorded before slice 3; test files were new (N/A correct) |

**TDD Compliance**: 6/6 checks passed. Apply-progress memo proof is non-vacuous (count==1 fails when memo hit disabled — documented empirically).

### Test Layer Distribution
| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit / service (SessionLocal + real Postgres, no HTTP) | 15 | 2 (`test_bom.py` validators 3, `test_costos.py` service 12) | pytest |
| Integration (TestClient + real Postgres + JWT tokens) | 54 | 3 (productos 24, bom 24, costos endpoint 6) | FastAPI TestClient |
| E2E | 0 | 0 | not applicable (backend API) |
| **Total** | **69** | **3** | |

### Changed File Coverage
Coverage analysis skipped — no coverage tool detected (pytest-cov not installed in backend/.venv). Informational only, not a failure.

### Assertion Quality
**Assertion quality**: ✅ All assertions verify real behavior — no banned patterns (no tautologies, no type-only assertions, no ghost loops, no smoke-only tests) found across the 3 test files (1,944 lines). Memoization test proves behavior with a SQL event counter that demonstrably fails when memoization is disabled. Empty-list assertions (`rows == []` after DELETE) are real outcomes with non-empty companion assertions in the same test.

### Quality Metrics
**Linter**: ➖ Not available (no ruff/flake8 configured for this repo's test run)
**Type Checker**: ➖ Not available

### Issues Found
**CRITICAL**: None

**WARNING**:
1. Changed-file coverage unavailable (pytest-cov not installed) — no line/branch coverage evidence for the 8 new backend files. Informational per strict-TDD rules; non-blocking.

**SUGGESTION**:
1. Add a test that opens a `FOR UPDATE` transaction on insumo rows and calls `calcular_costo_produccion` inside it, asserting it computes without extra locks/commits. The engine is structurally read-only (code-inspection verified), but a dedicated test would protect the Phase-4 reuse contract against future regressions.
2. `create_producto`/`update_producto` carry a defensive `IntegrityError → 409` branch that is currently dead code: `Productos.nombre` has no unique constraint (documented deviation from slice 1), so no commit-time uniqueness violation can occur. Remove the branch or document it as a future-proofing guard.
3. `CostoLineaRead.tipo` is typed as plain `str`; consider `Literal["insumo","producto","operativos_fijos"]` for a self-documenting API contract.
4. The `variante_id` query parameter on `GET /productos/{id}/costo` is a tested extension beyond the written spec scenario (design decision 7). If it is intended public API, reflect it in the costos-produccion spec.
5. `Producto.bom_insumos` lazy="selectin" fires an extra BOM_Insumos query on every `db.get(Producto, ...)` (apply-progress issue). Harmless for correctness, but consider it when profiling Phase-4 explosion performance.
6. apply-progress reports "25/25" tasks for slices 1–3; the authoritative tasks artifact contains 24 implementation tasks (9+8+7). Update the apply-progress count to 24/24 for consistency.

### Verdict
**PASS**
Full suite green (122/122, exit 0), 44/44 spec scenarios compliant, 24/24 implementation tasks complete, design decisions 12/12 followed, no CRITICAL findings, no regressions, clean working tree on the stacked branch. One informational WARNING (coverage tooling absent) and six non-blocking SUGGESTIONs.

**next_recommended**: sdd-archive
