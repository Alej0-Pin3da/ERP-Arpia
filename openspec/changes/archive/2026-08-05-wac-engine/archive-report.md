# Archive Report: WAC — Cost Engine & Purchase Registration (wac-engine)

**Change**: `wac-engine` (Fase 2)
**Status**: CLOSED — archived
**Archive date**: 2026-08-05
**Archived to**: `openspec/changes/archive/2026-08-05-wac-engine/`
**Mode**: hybrid (OpenSpec filesystem sync + Engram persistence)
**Review gate**: `reviewGate.delivery: disabled/unmanaged` — receipt-driven native review disabled by maintainer kill-switch; archive proceeds with delivery unmanaged (skill relaxation for `disabled/unmanaged`).
**Cycle**: SDD complete — proposed, speced, designed, implemented (10/10 tasks), verified, archived.

## Close State

Phase 2 delivered the first write path over `Insumos.stock_actual` / `costo_promedio_actual`: a WAC service (`registrar_compra`) that registers a `CompraInsumo` and recomputes weighted-average cost inside one atomic transaction guarded by `SELECT ... FOR UPDATE`, plus thin `POST`/`GET /api/v1/compras-insumos` routes. Specs are the new canonical baseline for the `compras-insumos` and `wac-engine` capabilities.

## Requirements Archived (8/8 — 23/23 scenarios)

| Capability | Requirements | Scenarios | Verdict |
|------------|--------------|-----------|---------|
| `wac-engine` | 4 (WAC-1..WAC-4) | 11 | PASS (10 compliant, 1 partial) |
| `compras-insumos` | 4 (CI-1..CI-4) | 12 | PASS (12 compliant) |

Synced to canonical specs:
- `openspec/specs/wac-engine/spec.md` — Created (full spec copy)
- `openspec/specs/compras-insumos/spec.md` — Created (full spec copy)

`openspec/specs/` was empty before this change; the delta specs are full specs, so they were copied directly (no ADDED/MODIFIED/REMOVED merge, no destructive delta — config `rules.archive` warn rule not triggered).

## Verification Evidence

Per `verify-report` (#348, 2026-08-05) with final-state confirmation from the orchestrator launch prompt (outranks intermediate snapshots):

- Verdict: **PASS WITH WARNINGS** — 0 CRITICAL, 0 blockers, `evidence_revision sha256:f571d4...3206` admitted by the verify validator.
- **10/10 tasks** complete (`tasks.md` all `[x]`; apply-progress #346 10/10).
- **53/53 tests passing, verified twice** (29 change tests: `test_wac.py` 13 + `test_compras_insumos.py` 16; 24 baseline) plus **4 extra concurrency runs** stable (2/2 green each). Real test PostgreSQL (localhost:5433), no mocks for business logic.
- Build/import check exit 0 (`from app.main import app` → OK).
- Compliance matrix: 22/23 scenarios fully compliant, 1 PARTIAL (see Warning 2). 0 UNTESTED, 0 FAILING.
- Coverage/linter/type-checker: not available (no pytest-cov / ruff / mypy) — not a failure.
- Scope drift: none — no edits to models, README, `.env`, or migrations (git status only `M router.py`, `M conftest.py` + untracked new files).

## Known Warnings Carried Forward (non-blocking)

1. **D4 deviation — `IntegrityError` → 409** (`backend/app/services/wac.py:60-66`) instead of design.md D4's "propagate as 500". Spec-neutral improvement; the design's own open question ("Confirm 409 vs 500") was deliberately resolved to 409 in `tasks.md` 2.2. No requirement broken.
2. **WAC-3 "Concurrency test requirement" PARTIAL** — spec literal says "concurrent POSTs"; covering test (`test_concurrent_purchases_same_insumo`) issues concurrent **service** calls with per-thread sessions against real Postgres. Substitution is design-documented (TestClient is synchronous, not reliable for parallel request threads). Required assertions (final stock+cost == serialized result, no lost update) fully proven.
3. **TDD evidence presented in prose**, not the prescribed 5-column "TDD Cycle Evidence" table (format-only; substance verified independently).

### Suggestions (non-blocking, optional hardening)

- `tests/test_compras_insumos.py:253` — self-referential assertion (`rows` IS `resp.json()`); redundant.
- No explicit admin-role POST test (admin shares `require_roles("admin","operador")` with operador; code-inspection only).
- GET `limit` unbounded (default 50, no max cap) — potential inexpensive DoS vector; consider `le=100`.
- Route-level 422 tests assert status only, not "no DB write" (pydantic rejection structurally prevents writes).

## Delivery State (UNCOMMITTED — next step outside archive)

**Nothing committed, no branches, no PRs.** All code + OpenSpec change artifacts remain in the working tree:

- Modified: `backend/app/api/router.py`, `backend/tests/conftest.py`
- Untracked: `backend/app/services/` (wac.py), `backend/app/schemas/compra_insumo.py`, `backend/app/api/routes/compras_insumos.py`, `backend/tests/test_wac.py`, `backend/tests/test_compras_insumos.py`, `openspec/`

Delivery plan (per preflight decision #338, stacked-to-main): **PR 1** = schemas + WAC service + service tests; **PR 2** = routes + wiring + endpoint tests. 400-line budget risk High → 2-PR chain. Review mode OFF; delivery unmanaged.

## Review State

Receipt-driven native review is **disabled/unmanaged** per maintainer kill-switch decision; no native review governs this change and archive proceeds without it. Prior context: native review was attempted and blocked by a gentle-ai 2.2.4 binding-lens failure (`GENTLE_AI_REVIEW_BINDING` rejection, #347) — the maintainer then disabled receipt-driven review rather than re-enable it. Do NOT start or re-enable native review; this kill-switch decision is the standing configuration.

## Engram Traceability (observation IDs)

| Artifact | Observation | Sync ID |
|----------|-------------|---------|
| proposal | #342 | obs-998655d756d351c6 |
| spec | #343 | obs-6532a916fcd80101 |
| design | #344 | obs-68455f44b2b7a132 |
| tasks | #345 | obs-5520c5881af3f81d |
| apply-progress | #346 | obs-537efc51f6b6cfeb |
| verify-report | #348 | obs-fc7db27299ada050 |
| review block context (pre-kill-switch) | #347 | obs-0c42edc1f2b50c38 |
| preflight delivery decision (stacked-to-main) | #338 | obs-ee841e743ba9a2ac |
| archive-report | topic `sdd/wac-engine/archive-report` | (this report) |

## Follow-ups for Next Phases

- Phase 3 (BOM) will own the master-unit + conversion-factor design (cm→m); Phase 2 keeps single-master-unit math.
- Phase 4 must consume `costo_promedio_actual` for `costo_unitario_aplicado` snapshots — engine precision (no rounding, NUMERIC(15,4)) preserved for that downstream.
- Optional hardening suggestions above are backlog material, not blockers.
- Delivery (2 stacked PRs) is the immediate next step after archive.
