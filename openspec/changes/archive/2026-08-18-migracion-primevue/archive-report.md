# Archive Report: Frontend Migration Element Plus → PrimeVue 4.5.5 (MIT) — migracion-primevue

**Change**: `migracion-primevue`
**Project**: ERP-Arpia (`C:\wamp64\www\ERP-Arpia`)
**Status**: CLOSED — archived
**Archived at**: 2026-08-18
**Archived to**: `openspec/changes/archive/2026-08-18-migracion-primevue/`
**Store**: hybrid (OpenSpec filesystem archive + Engram persistence)
**Review gate**: No native review governs this change (standing unmanaged delivery posture, consistent with prior archived changes). The runtime ledger verify attempt settled `complete`; archive is not runtime-bearing and required no new attempt per the dispatcher instructions.
**Cycle**: SDD complete — proposed, explored, speced, designed, implemented (48/48 tasks), verified (PASS), archived.

## Close State

The ERP-Arpia frontend migrated from Element Plus 2.9.3 (full-bundle global registration) to PrimeVue 4.5.5 (exact pin, last MIT release) with per-component imports, delivered as 6 slices / 11 chained PRs, all merged to `main` (main = d2ca87b; PR #36 merged by maintainer 2026-08-19 04:03Z). Element Plus is fully removed: zero `el-*`/`element-plus`/`plugins:[ElementPlus]` code references remain in `frontend/` (5 historical comments only). User-observable behavior, dark editorial theme (`definePreset(AuraCompat)` driven by the `--arpia-*` brand vars), es-CO locale, 403 toast, login validation, and the full vitest suite are preserved and green.

## Capabilities Archived

**None.** This is a pure framework refactor — the spec is a standalone migration document (`spec.md`) with NO delta target to merge. All 7 main capability specs (`openspec/specs/*`: wac-engine, ventas-variantes, productos, migracion-catalogos, costos-produccion, bom, compras-insumos) are backend domains untouched by this change. No ADDED/MODIFIED/REMOVED merge was performed; config `rules.archive` warn rule not triggered.

## Verification Evidence (final state at close)

Final-state facts from the orchestrator launch prompt and repository evidence (authoritative over the intermediate `apply-progress` #519 snapshot, written before slice 5 merged):

- **Verdict**: PASS — `verify-report.md` committed at 2bcf494, schema `gentle-ai.verify-result/v1`, 11/11 requirements, 12/12 scenarios, `evidence_revision sha256:5be115efc6001c0d992fbde32520c741104fa4f6438c3022883fbcb326efef45` (sha256 of `git ls-tree -r HEAD` at d2ca87b). No CRITICAL, no WARNING blockers.
- **PR #36 merged by maintainer 2026-08-19 04:03Z** — slice 5 (drop Element Plus) is in main (main = d2ca87b). Zero `el-*`/`element-plus`/`plugins:[ElementPlus]` code refs remain (5 historical comments only).
- **Build size after EP drop**: main chunk 1,410.53 kB (gzip 382.45 kB), measured 2026-08-19 — well under budget 2,585.46 kB (baseline 2,350.42 × 1.10). Bundle REDUCED by ~940 kB vs baseline (MIG-3 met).
- **Suite**: 59 files / 546 tests green (final gate, run on main), exit 0 (MIG-4 met).
- **Diff isolation (MIG-1)**: migration range `2ad2002~1..d2ca87b` — 116 files, all under `frontend/` or `openspec/`; zero backend/API/data-semantics changes.

## Commits (11 merged PRs, stacked-to-main)

All slices merged to main via the chained PRs #26..#36 (slice 0 → PR #26 … slice 4b → PR #35, slice 5 → PR #36; main = d2ca87b). Docs commits on top: `c82f6cc` (slice-5 task marks), `f00579f` (S4-T7 QA sign-off), `2bcf494` (verify-report).

## Task Reconciliation

No reconciliation needed: `tasks.md` shows 48/48 implementation tasks `[x]` at archive time. Task Completion Gate passed as-is.

## Known Pre-existing Conditions (documented, NOT this change's regressions)

1. **Backend ruff format failure on main** (`backend/migrate/sales.py` + `tests/test_migrate_sales.py`, commits 27d985a/870bdf7 in main) — keeps CI Backend red on every PR; pre-existing, unrelated to this frontend-only change.
2. **vue-tsc baseline typecheck errors** — the repo has no vue-tsc/typecheck script; vue-tsc 2.x fails at baseline on pre-existing issues (~150 errors at f00579f: generated `api.d.ts` exposes no top-level `*Read` types, endpoint generics, DataTable event typings). Slice-5-introduced parse failures (inline typed template arrows) were fixed by converting 11 handlers to named script functions. Documented in the S5-T2 note.

## Rollback Notes

Each slice shipped as its own PR in the chain — revert the offending PR; Element Plus stayed functional through slice 4 via dual registration. Slice 5 (PR #36) is the only destructive step; reverting it restores dual registration.

## Review State

No native review governs this change (standing unmanaged delivery posture, same as the prior archived changes wac-engine, producto-bom-multinivel, tallas-variantes-xxs-xl). Runtime ledger: the verify attempt settled `complete`; no new attempt required for archive.

## Engram Traceability (observation IDs)

| Artifact | Observation | Sync ID |
|----------|-------------|---------|
| explore | #510 | obs-8e565587ae62d5ae |
| proposal | #513 | obs-25f77878ada359e6 |
| spec | #514 | obs-461b4aa5fe83f050 |
| design | #516 | obs-0eb912f5922c375e |
| tasks | #518 | obs-8cbcf77ffac5f040 |
| apply-progress | #519 | obs-05cf4beee76e3639 |
| verify-report | #535 | obs-cf6e21806e0a15f2 |
| archive-report | topic `sdd/migracion-primevue/archive-report` | (this report) |

## Follow-ups (recorded as notes — NOT blockers)

- **Backend ruff format**: fix the pre-existing format failures in `backend/migrate/sales.py` + `tests/test_migrate_sales.py` (on main since 27d985a/870bdf7).
- **Typecheck**: add a vue-tsc/typecheck script and resolve the ~150 baseline errors in a separate change (the repo has no typecheck script today).
- Optional hardening (verify-report SUGGESTION): add a unit spec asserting the es-CO paginator/aria label strings (direct runtime assertion for the BEH-7 "Paginator labels" scenario); add `.idea/` to `.gitignore`; optionally sweep the historical `el-*`/`element-plus` mentions that remain in code comments only.
