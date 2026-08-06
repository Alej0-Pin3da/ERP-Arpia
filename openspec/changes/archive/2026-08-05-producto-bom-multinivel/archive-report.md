# Archive Report: Product Engineering & Multilevel BOM (producto-bom-multinivel)

**Change**: `producto-bom-multinivel` (Fase 3)
**Status**: CLOSED — archived
**Archive date**: 2026-08-05
**Archived to**: `openspec/changes/archive/2026-08-05-producto-bom-multinivel/`
**Mode**: hybrid (OpenSpec filesystem sync + Engram persistence)
**Review gate**: `reviewGate.delivery: disabled/unmanaged` — receipt-driven native review disabled by maintainer kill-switch (standing configuration inherited from the wac-engine change); archive proceeds with delivery unmanaged (skill relaxation for `disabled/unmanaged`).
**Cycle**: SDD complete — proposed, speced, designed, implemented (24/24 implementation tasks + 2/2 verify-phase tasks), verified, archived.

## Close State

Phase 3 delivered the full product engineering surface over the Phase-1 models (no migration, no model edits): master CRUD for `Tipos_Producto` / `Productos` / `Variantes_Producto` (nested), recipe CRUD for `BOM_Insumos` (variante-specific, waste %) and `BOM_Productos` (combos) with explicit duplicate-rule validation, and a read-only recursive memoized production-cost engine (`services/costos.py`) exposed via `GET /productos/{id}/costo` (total + 1-level breakdown). The engine is Phase-4-reusable inside its own `FOR UPDATE` transactions. Implemented as three stacked slices mapping 1:1 to chained PRs.

## Requirements Archived (14/14 — 44/44 scenarios)

| Capability | Requirements | Scenarios | Verdict |
|------------|--------------|-----------|---------|
| `productos` | 4 (Tipo_Producto CRUD, Producto CRUD, Variante_Producto nested CRUD, Authorization) | 15 | PASS (15 compliant) |
| `bom` | 5 (BOM_Insumos CRUD, Duplicate insumo-line rule, Variante semantics, Waste semantics, BOM_Productos CRUD) | 14 | PASS (14 compliant) |
| `costos-produccion` | 5 (Recursive memoized cost service, Cycle detection, Non-fabricated/no-BOM rule, Cost endpoint, Read-only Phase-4 reuse contract) | 15 | PASS (15 compliant) |

Specs synced to canonical specs — **already full specs, verified identical** (SHA-256 match at archive time, no ADDED/MODIFIED/REMOVED merge required):
- `openspec/specs/productos/spec.md` — full spec copy (already in sync)
- `openspec/specs/bom/spec.md` — full spec copy (already in sync)
- `openspec/specs/costos-produccion/spec.md` — full spec copy (already in sync)

These delta specs are full specs (not deltas); the main specs were synced during apply (docs commit `95dd391`) and verified hash-identical at archive time. No destructive delta — config `rules.archive` warn rule not triggered.

## Verification Evidence (final state at close)

Final-state facts from the orchestrator launch prompt (outrank intermediate snapshots `apply-progress` #361 and `verify-report` #363, both written before the final verification run):

- Verdict: **PASS** — full suite **122/122 green** (exit 0, ~19.8s), **0 regressions**, **0 CRITICAL**, **1 WARNING** (changed-file coverage unavailable: pytest-cov not installed — informational per strict-TDD rules), **6 SUGGESTIONS** (non-blocking hardening/backlog).
- **Change-specific tests: 69/69** (24 `test_productos.py` + 27 `test_bom.py` + 18 `test_costos.py`), against real test PostgreSQL (no business-logic mocks).
- **Tasks: 24/24 implementation tasks (1.1–3.7) + 2/2 verify-phase tasks (4.1–4.2)** complete. Phase-4 tasks were executed and passed by the verification run itself (full suite green; router ordering/tags verified via app-import probe: `from app.main import app` → OK, 59 total API routes live, no path collisions).
- Spec compliance: **44/44 scenarios COMPLIANT**, 0 PARTIAL, 0 UNTESTED, 0 FAILING; design decisions 12/12 followed.
- Build check: exit 0; route probe confirms nested variantes (4), BOM insumos (4), BOM productos (4), `/productos/{id}/costo` (1) live.
- Post-suite DB state: 0 leftover rows in all Phase-3 tables (cleanup helpers verified).

> **SUGGESTION-6 resolution (task-count discrepancy)**: `apply-progress` #361 reports "25/25" tasks for slices 1–3, but the authoritative tasks artifact contains **24 implementation tasks (9 + 8 + 7)** plus **2 verify-owned Phase-4 tasks (4.1–4.2)**. The archive records **24/24 implementation tasks + 2/2 verify tasks = 26/26 total checkboxes complete**. Apply-progress count was a labeling discrepancy, not missing work.

## Task Reconciliation Record (archive-time, exceptional)

Phase-4 tasks 4.1/4.2 were left `- [ ]` in `tasks.md` at apply time because verification owns them (they are not implementation tasks). Both were executed and passed by the verification run (per verify-report Completeness table: "Verify-phase tasks (4.1–4.2): 2 — both executed and passed by THIS verification"; 122/122 full suite exit 0; router probe). Per the Task Completion Gate's exceptional reconciliation path — orchestrator explicitly instructed the final state (24/24 implementation + verify tasks complete) and verify-report proves completion — the checkboxes were marked `[x]` at archive time so the archived audit trail contains no stale unchecked tasks for completed work. Reconciliation note recorded inline in the archived `tasks.md`.

## Known Warnings / Suggestions Carried Forward (non-blocking)

1. **WARNING (only)**: Changed-file coverage unavailable — pytest-cov not installed in `backend/.venv`; no line/branch coverage evidence for the 8 new backend files. Informational; not a failure.
2. **SUGGESTION-1**: Add a regression test calling `calcular_costo_produccion` inside a `FOR UPDATE` locked transaction (engine is structurally read-only — code-inspection verified, zero `with_for_update`/`commit`/`rollback` in `services/costos.py`).
3. **SUGGESTION-2**: `create_producto`/`update_producto` carry a defensive `IntegrityError → 409` branch that is currently dead code (`Productos.nombre` has no unique constraint — documented deviation from slice 1). Remove or document as future-proofing.
4. **SUGGESTION-3**: `CostoLineaRead.tipo` typed as plain `str`; consider `Literal["insumo","producto","operativos_fijos"]`.
5. **SUGGESTION-4**: `variante_id` query param on `GET /productos/{id}/costo` is a tested extension beyond the written spec scenario (design decision 7); reflect in the costos-produccion spec if intended public API.
6. **SUGGESTION-5**: `Producto.bom_insumos` lazy="selectin" fires an extra BOM_Insumos query per `db.get(Producto, ...)`; consider when profiling Phase-4 explosion performance.

## Delivery State (COMMITTED on stacked branches — NOT pushed, NOT PR'd)

Branch chain (stacked-to-main, per cached delivery decision from wac-engine #338):

- `feat/phase3-producto-slice1` → `34ba8b1` "feat: CRUD de tipos, productos y variantes (fase 3 slice 1)"
- `feat/phase3-bom-slice2` → `2b28cc2` "feat: gestion de recetas BOM con insumos, variantes y combos (fase 3 slice 2)" (base `34ba8b1`)
- `feat/phase3-costos-slice3` → `555e7a7` "feat: motor de costos de produccion recursivo con memoizacion (fase 3 slice 3)" (base `2b28cc2`) — **current tip**

Also on the chain: `95dd391` "docs: artefactos openspec del cambio producto-bom-multinivel" (proposal, specs, design, tasks).

Post-commit artifacts (untracked at archive time): `verify-report.md` and the archived change folder — the orchestrator's delivery step commits them. Review mode OFF; delivery unmanaged. **Do NOT push or PR from the archive phase** — orchestrator handles delivery after archive.

## Review State

Receipt-driven native review is **disabled/unmanaged** per maintainer kill-switch decision (standing configuration from the wac-engine change); no native review governs this change and archive proceeds without it. No `reviews/` directory and no `sdd/producto-bom-multinivel/review/*` Engram topics exist — consistent with the unmanaged delivery state. Do NOT start or re-enable native review.

## Engram Traceability (observation IDs)

| Artifact | Observation | Sync ID |
|----------|-------------|---------|
| proposal | #356 | obs-aa3d6bed3ec41655 |
| spec | #357 | obs-48bf108c8c00f8ad |
| design | #358 | obs-7a142711df51bd6d |
| tasks | #359 | obs-3c862fb389100e84 |
| apply-progress (merged slices 1–3) | #361 | obs-72bb42b0c9f65aee |
| verify-report | #363 | obs-d2bba9b03d3bc98f |
| archive-report | topic `sdd/producto-bom-multinivel/archive-report` | (this report) |

## Follow-ups for Next Phases

- **Delivery (immediate next step)**: orchestrator opens 3 chained PRs (productos → bom → costos) per the stacked-to-main plan and delivers the branch chain. Slice branches must NOT be deleted by the archive phase.
- Phase 4 (explosion/margins) must consume `calcular_costo_produccion` inside its own `FOR UPDATE` transaction — engine precision (`Decimal` / `NUMERIC(15,4)`, no engine rounding, e.g. 66.66665) preserved for that downstream.
- Optional hardening suggestions (1–5 above) are backlog material, not blockers.
- Post-slice cleanup opportunity: re-evaluate `Producto.bom_insumos` selectin loading before Phase-4 performance work (SUGGESTION-5).
