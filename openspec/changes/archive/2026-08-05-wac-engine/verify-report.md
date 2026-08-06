```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:f571d490251469c88a790514a25aac094ae466192a76f1855234d64b77fd3206
verdict: pass
blockers: 0
critical_findings: 0
requirements: 8/8
scenarios: 23/23
test_command: C:\wamp64\www\ERP-Arpia\backend\.venv\Scripts\python.exe -m pytest tests -q
test_exit_code: 0
test_output_hash: sha256:f571d490251469c88a790514a25aac094ae466192a76f1855234d64b77fd3206
build_command: C:\wamp64\www\ERP-Arpia\backend\.venv\Scripts\python.exe -c "from app.main import app; print('app imported OK')"
build_exit_code: 0
build_output_hash: sha256:bf7b7cb5f051d4446847c1ca9a5dafee2152484a2fbcca46f65fa8c780a49f8d
```

## Verification Report

**Change**: wac-engine (Fase 2 — WAC Cost Engine & Purchase Registration)
**Version**: N/A (first change; capabilities are new)
**Mode**: Strict TDD (runner: pytest 8.3.4 via backend/.venv, Python 3.11.9)
**Date**: 2026-08-05
**Work unit**: feat/phase2-wac-verify

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 10 |
| Tasks complete | 10 |
| Tasks incomplete | 0 |

All 10 tasks `[x]` in `openspec/changes/wac-engine/tasks.md`; apply-progress reports 10/10 with per-phase RED→GREEN evidence. Task 4.1 (full suite twice) independently reproduced below.

### Build & Tests Execution

**Build / import check**: ✅ exit 0
```text
python -c "from app.main import app; print('app imported OK')"   →  app imported OK
```

**Tests (run 1)**: ✅ 53 passed, 0 failed, 0 skipped — `pytest tests -q` → `53 passed in 7.29s`
**Tests (run 2)**: ✅ 53 passed, 0 failed, 0 skipped — `pytest tests -q` → `53 passed in 7.32s`

Breakdown (reproduced): `test_wac.py` 13 passed · `test_compras_insumos.py` 16 passed · baseline (remaining 24 tests) 24 passed = **53 total**. Concurrency tests (`-k "concurrent or parallel"`) stable across 4 extra runs (2/2 green each).

**Coverage**: ➖ Not available — no `pytest-cov` installed (not a failure).

### Spec Compliance Matrix

Counts derived from the two retrieved specs: **8 requirements, 23 scenarios** (wac-engine: 4 reqs / 11 scenarios; compras-insumos: 4 reqs / 12 scenarios) plus 1 decision.

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| WAC-1 Atomic WAC in the purchase transaction | Atomic commit | `tests/test_wac.py::test_purchase_atomic_write_commits_stock_and_cost`; endpoint-level `test_compras_insumos.py::test_post_operador_201` | ✅ COMPLIANT |
| WAC-1 | All-or-nothing rollback | `tests/test_wac.py::test_rollback_on_error_leaves_unmodified`; `::test_integrity_error_maps_to_409` (asserts stock/cost/purchases unchanged) | ✅ COMPLIANT |
| WAC-2 Weighted-average cost formula | Equal unit price keeps cost stable | `tests/test_wac.py::test_wac_equal_prices_keeps_cost_stable` | ✅ COMPLIANT |
| WAC-2 | Price fluctuation moves the average | `tests/test_wac.py::test_wac_price_fluctuation_moves_average` (stock 20.0000 / cost 7.0000 — matches spec figures) | ✅ COMPLIANT |
| WAC-2 | Cost rises on higher-priced lot | `tests/test_wac.py::test_wac_higher_priced_lot_raises_cost` (100@5 + 50@8 → 6.0000) | ✅ COMPLIANT |
| WAC-3 Row locking for concurrency | Concurrent same-insumo purchases stay consistent | `tests/test_wac.py::test_concurrent_purchases_same_insumo` (threads + Barrier, per-thread SessionLocal, real Postgres; final stock==20==sum, cost==7 serialized, 2 rows) | ✅ COMPLIANT |
| WAC-3 | Different insumos run in parallel | `tests/test_wac.py::test_different_insumos_run_in_parallel` | ✅ COMPLIANT |
| WAC-3 | Concurrency test requirement (literal: "concurrent POSTs") | `tests/test_wac.py::test_concurrent_purchases_same_insumo` — concurrent **service** calls, not HTTP POSTs; design-documented substitution (TestClient not reliable for parallel request threads, design.md Test Plan Mapping). Required assertions (serialized stock+cost, no lost update) fully proven | ⚠️ PARTIAL |
| WAC-4 Edge cases and precision | Zero prior stock | `tests/test_wac.py::test_wac_zero_stock_yields_unit_price` (→ 7.0000) | ✅ COMPLIANT |
| WAC-4 | Precision preserved | `tests/test_wac.py::test_wac_precision_no_engine_rounding` (42/13 = 3.230769… stored as 3.2308; engine never quantizes) | ✅ COMPLIANT |
| WAC-4 | Precondition before writes | `test_wac.py::test_nonexistent_insumo_returns_404`, `::test_nonexistent_proveedor_returns_400`; `test_compras_insumos.py::test_create_nonexistent_insumo_404`, `::test_invalid_quantity_422`, `::test_invalid_price_422` | ✅ COMPLIANT |
| CI-1 Register an insumo purchase | Create with optional proveedor | `test_compras_insumos.py::test_post_operador_201`; `test_wac.py::test_purchase_with_valid_proveedor_commits` | ✅ COMPLIANT |
| CI-1 | Purchase without proveedor | `test_compras_insumos.py::test_post_without_proveedor_201` (proveedor_id null) | ✅ COMPLIANT |
| CI-1 | Nonexistent insumo | `test_compras_insumos.py::test_create_nonexistent_insumo_404` | ✅ COMPLIANT |
| CI-1 | Invalid proveedor | `test_compras_insumos.py::test_invalid_proveedor_400` | ✅ COMPLIANT |
| CI-1 | Non-positive quantity / negative price | `test_compras_insumos.py::test_invalid_quantity_422` (0, −5), `::test_invalid_price_422` (−1, "−0.01") | ✅ COMPLIANT |
| CI-2 Authorization | Unauthenticated POST | `test_compras_insumos.py::test_post_unauth_401` (+ `::test_get_unauth_401`) | ✅ COMPLIANT |
| CI-2 | Consulta POST forbidden | `test_compras_insumos.py::test_post_consulta_403` | ✅ COMPLIANT |
| CI-2 | Operador POST allowed | `test_compras_insumos.py::test_post_operador_201` | ✅ COMPLIANT |
| CI-2 | Any role reads | `test_compras_insumos.py::test_get_consulta_200` (consulta 200; operador GET in list tests) | ✅ COMPLIANT |
| CI-3 List with pagination and filter | Paginated list | `test_compras_insumos.py::test_list_paginated_limit_offset` (limit=2&offset=2 → exactly ids 3–4); `::test_list_ordered_by_id` (ordering by id) | ✅ COMPLIANT |
| CI-3 | Filter by insumo | `test_compras_insumos.py::test_list_filter_by_insumo` | ✅ COMPLIANT |
| CI-4 Response shape | Read shape completeness | `test_compras_insumos.py::test_read_shape_completeness` (id, insumo_id, proveedor_id, fecha_compra, cantidad, precio as Decimal strings) | ✅ COMPLIANT |
| Decision: no `fecha_compra` range filter this phase | — | Static: GET signature exposes only `limit`/`offset`/`insumo_id` (compras_insumos.py:33-37) | ✅ COMPLIANT (static) |

**Compliance summary**: 23/23 scenarios have passing covering tests (22 fully compliant, 1 ⚠️ PARTIAL per WAC-3 concurrency mechanism) — 0 UNTESTED, 0 FAILING.

### Correctness (Static Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| Atomicity (FOR UPDATE + single transaction) | ✅ Implemented | `wac.py:30-32` `select(Insumo).where(id==...).with_for_update()`; `wac.py:57` single `db.commit()`; `wac.py:67-69` rollback+re-raise on any exception; `wac.py:60-66` IntegrityError → 409 (no 500 leak). HTTPException 404/400 raised inside try → rollback path still runs |
| Authz (roles) | ✅ Implemented | `compras_insumos.py:12-13` audited_user (admin/operador/consulta) for GET, mutation_user (admin/operador) for POST; `deps.py:59-68` 401 no-token, 403 wrong role |
| Pagination | ✅ Implemented | `compras_insumos.py:34` limit=50 default / offset=0; `:43` `.limit().offset()` after `order_by(id)` |
| Filters | ✅ Implemented | `compras_insumos.py:41-42` optional `insumo_id` WHERE; no date-range filter (per spec decision) |
| Error codes 404/400/422 | ✅ Implemented | 404 `wac.py:34`; 400 `wac.py:39`; 422 via pydantic `Field(gt=0)`/`Field(ge=0)` (compra_insumo.py:10-11) before service call; 409 IntegrityError `wac.py:63-66` |
| Decimal precision / no rounding | ✅ Implemented | `wac.py:26-27` Decimal(str(...)); `:43-45` WAC formula in Decimal, no quantize; storage NUMERIC(15,4) (models/insumos.py:67-69); pydantic serializes Decimal as string |
| Unit handling | ✅ Implemented | Single-master-unit per proposal stance: purchase recorded in `unidad_medida` master unit; no conversion factor (deferred to Phase 3 BOM) — `unidad_medida="metro"` in test fixtures |
| `fecha_compra` server-set | ✅ Implemented | Model `server_default=func.now()` (models/insumos.py:65); route omits client value → DB sets it (equivalent to design flow's explicit `func.now()`) |
| FK semantics | ✅ Implemented | insumo_id FK RESTRICT non-null (models/insumos.py:59); proveedor_id FK SET NULL nullable (:62) |

### Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| D1 Service location `app/services/wac.py` + `registrar_compra` | ✅ Yes | Exact signature match: `registrar_compra(db, insumo_id, proveedor_id, cantidad, precio_unitario) -> CompraInsumo` (wac.py:11-17) |
| D2 Session in / ORM CompraInsumo out | ✅ Yes | Route maps ORM → schema via response_model (compras_insumos.py:16) |
| D3 Validation boundary (422 pydantic → service 404/400) | ✅ Yes | compra_insumo.py:10-11; wac.py:34,39 |
| D4 Error/rollback contract | ⚠️ Deviation | Single commit + rollback+re-raise: yes. **IntegrityError → 409** (wac.py:60-66) instead of design's chosen "propagate as 500". Spec-neutral improvement; the design's own open question ("Confirm 409 vs 500") was resolved to 409 in tasks.md 2.2. No spec broken |
| D5 Row locking `SELECT ... FOR UPDATE` | ✅ Yes | `db.scalar(select(...).with_for_update())` (wac.py:30-32) — scalar() executes the statement, equivalent to design's db.execute |
| D6 Decimal policy, no engine rounding | ✅ Yes | wac.py:26-27,43-45; NUMERIC(15,4) storage; 2dp only at presentation |
| D7 Pessimistic locking, no retry loop | ✅ Yes | FOR UPDATE only; no optimistic/retry path |
| Transaction boundaries (single commit; rollback on failure) | ✅ Yes | One commit at wac.py:57; rollback on IntegrityError (:62) and any Exception (:68) |

**Scope drift check**: No edits to models, README, `.env`, or migrations (git status: only `M router.py`, `M conftest.py`; new files untracked). Out-of-scope items (sales, BOM, returns, UI, date-range filter) not introduced.

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ | apply-progress reports RED→GREEN per task in **prose** (2.1/2.3/3.1 RED written, 2.2/3.2/3.4 GREEN passed, triangulation cases, safety-net runs), but not as the prescribed "TDD Cycle Evidence" table with column rows |
| All tasks have tests | ✅ | 10/10 — tasks 1.1–3.4 backed by `test_wac.py`/`test_compras_insumos.py`; 4.1–4.2 are verification/housekeeping (covered by full-suite runs) |
| RED confirmed (tests exist) | ✅ | 2/2 test files exist and were created before GREEN (per apply-progress ordering) |
| GREEN confirmed (tests pass) | ✅ | 29/29 change tests + 24 baseline = 53 pass on independent execution (2 runs) |
| Triangulation adequate | ✅ | 13 service tests across 4 WAC requirements; 16 endpoint tests across 4 CI requirements; multiple distinct expected values per behavior |
| Safety Net for modified files | ✅ | `conftest.py` (test infra) modified; full-suite double-run (53/53) exercised baseline as safety net. `router.py` change covered by every suite run |

**TDD Compliance**: 5/6 checks passed (evidence-presentation format warning only).

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit / service | 13 | 1 (`test_wac.py`) | pytest 8.3.4, real test Postgres |
| Integration | 16 | 1 (`test_compras_insumos.py`) | pytest + FastAPI TestClient + real test Postgres |
| E2E | 0 | 0 | not installed |
| **Total** | **29** | **2** | |

All change tests hit the real PostgreSQL test DB (localhost:5433) — no mocks for the business logic.

### Changed File Coverage

**Coverage analysis skipped — no coverage tool detected** (`pytest-cov` not installed). Not a failure.

### Assertion Quality

| File | Line | Assertion | Issue | Severity |
|------|------|-----------|-------|----------|
| `tests/test_compras_insumos.py` | 253 | `assert rows[0]["id"] == resp.json()[0]["id"]` | Self-referential — `rows` IS `resp.json()`, always true; redundant (test still meaningful via `len(rows)==1` + `insumo_id` asserts) | SUGGESTION |

No tautologies, no orphan empty checks, no ghost loops (setup loops use fixed `range()`), no type-only-only assertions, no smoke tests, no implementation-detail coupling. Mock/assertion ratio healthy (1 monkeypatch in `test_integrity_error_maps_to_409` vs 4+ value assertions). Concurrency assertions robust to either thread serialization order (both orders yield cost 7).

**Assertion quality**: 0 CRITICAL, 0 WARNING, 1 SUGGESTION

### Quality Metrics

**Linter**: ➖ Not available (no ruff)
**Type Checker**: ➖ Not available (no mypy)

### Issues Found

**CRITICAL**: None

**WARNING**:
1. Design D4 deviation — `IntegrityError` maps to **409** (`backend/app/services/wac.py:60-66`) while design.md D4 chose "propagate as 500". Resolved deliberately in tasks.md 2.2 ("resolve D4 open question: map to 409, no 500 leak"); spec-neutral, no requirement broken. Evidence: design.md:14, tasks.md:33, wac.py:60-66, test_wac.py:268-303.
2. WAC-3 "Concurrency test requirement" scenario partially conforms — spec says "concurrent POSTs"; covering test (`test_wac.py::test_concurrent_purchases_same_insumo`) issues concurrent **service** calls with per-thread sessions against real Postgres. Substitution is design-documented (design.md:65: TestClient is synchronous, not reliable for parallel request threads) and the required assertions (final stock+cost == serialized result, no lost update) are fully proven. Evidence: spec wac-engine:63-65, design.md:58,65, test_wac.py:342-378.
3. TDD evidence presented in prose, not the prescribed "TDD Cycle Evidence" table format (apply-progress lacks the formal 5-column table). Substance verified independently: test files exist, all pass, triangulation and safety-net present. Evidence: apply-progress (Engram #346), strict-tdd-verify.md:43-46.

**SUGGESTION**:
1. `tests/test_compras_insumos.py:253` — replace self-referential assertion with a real one (e.g., compare against `created_ids` ordering).
2. No explicit admin-role POST test; admin shares the same `require_roles("admin","operador")` dependency as operador (covered by code inspection only).
3. GET `limit` is unbounded (default 50, no max cap) — not in spec, but a large `limit` is an inexpensive DoS vector; consider a cap (e.g. `le=100`).
4. Route-level 422 tests assert the status code but not "no DB write" (service-level 404/400 tests do assert no write; pydantic rejection structurally prevents any write — optional hardening).

### Verdict

**PASS WITH WARNINGS** — 10/10 tasks complete; full suite green twice (53/53, stable, concurrency-stable); 8/8 requirements and 23/23 scenarios covered by passing tests (1 scenario partially covered by a design-documented substitution); no CRITICAL findings, no blockers. Warnings are design-deviation/noise-level and do not block archiving.
