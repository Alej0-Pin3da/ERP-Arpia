# Archive Report: Tallas de variantes (XXS–XL) — tallas-variantes-xxs-xl

**Change**: `tallas-variantes-xxs-xl`
**Project**: ERP-Arpia (`C:\wamp64\www\ERP-Arpia`)
**Status**: CLOSED — archived
**Archived at**: 2026-08-14
**Archived to**: `openspec/changes/archive/2026-08-14-tallas-variantes-xxs-xl/`
**Store**: hybrid (OpenSpec filesystem sync + Engram persistence)
**Review gate**: No native review was run for this change yet — PRs are pending delivery (see Delivery State). No `reviews/` directory and no `sdd/tallas-variantes-xxs-xl/review/*` Engram topics exist. Consistent with the standing unmanaged delivery posture of prior archived changes (wac-engine, producto-bom-multinivel).
**Cycle**: SDD complete — proposed, speced, designed, implemented (10/10 implementation tasks T1–T10 + Phase-6 verification task), verified, archived.

## Close State

This change seeded size variants **XXS–XL** for the sized garment catalog and wired historical VENTAS/PRENDAS sizes into the catalog + sales migration. F1 now seeds 30 variants across 5 sized products (Set Aelo, Set Ocipete, Set Celeno, Blusa Manga Larga, Blusa Manga Corta) with `precio_venta` NULL, adds the missing **Set Celeno** product at the locked price 75000 (catalog count 13→14), F5 omits + reports the 2 size-less sale rows (SET OCIPETE 28/3, BLUSA ARPIA MANGA LARGA 5/8) instead of hard-failing, gains one-direction NULL-matching idempotency so re-runs no longer duplicate the 21 historical sales, and F7 validation mirrors both semantics. The ventas frontend now requires a variant on any sized product line (VentasForm submit-block with warning), keeps combos as single-line NULL-variant, and loads variants lazily per product.

## Capabilities Archived (9/9 requirements — 17/17 scenarios)

| Capability | Requirements | Scenarios | Verdict |
|------------|--------------|-----------|---------|
| `migracion-catalogos` | 5 (MIG-1..MIG-5) | 10 | PASS (10 compliant) |
| `ventas-variantes` | 4 (VV-1..VV-4) | 7 | PASS (7 compliant) |

Specs synced to canonical specs — **both are NEW capabilities, full specs (not deltas); copied directly, verified SHA-256 identical at archive time**:
- `openspec/specs/migracion-catalogos/spec.md` — Created (full spec copy)
- `openspec/specs/ventas-variantes/spec.md` — Created (full spec copy)

No ADDED/MODIFIED/REMOVED merge required; no destructive delta — config `rules.archive` warn rule not triggered.

## Verification Evidence (final state at close)

Final-state facts from the orchestrator launch prompt (authoritative over intermediate snapshots `apply-progress` #502 and `verify-report` #503, both written before the final numbers below were confirmed):

- Verdict: **PASS** — 9/9 requirements, 17/17 scenarios PASS; success criteria all met; design decisions D1–D6 followed.
- **Backend**: 512 tests pass (change-relevant gate `-k` filters the 4 pre-existing `test_migrate_stock.py` alias failures, exit 0). Full unfiltered suite: 512 passed, 4 failed — the 4 failures verified **identical on main `408aeaf`** (`assert res["seteados"] == 1` → `assert 0 == 1`), NOT a regression of this change.
- **Frontend**: 498 vitest tests pass (55 files, exit 0); `vite build` green (exit 0, 9.23s; only pre-existing >500 kB chunk-size informational warning).
- **Lint**: `ruff check backend` clean; `npm run lint` clean.
- **Key success-criteria evidence**: 30 variants with `precio_venta` NULL (REAL-xlsx test `test_plan_catalogo_real_30_variantes_y_14_productos`); Set Celeno @75000 with `conteo_productos == 14`; F5 omits the 2 size-less rows + reports (product, date, qty, reason) with no `DomainValidationError` and idempotent re-run (`test_aplicar_ventas_omitida_sin_talla_no_estalla`, `test_aplicar_ventas_rerun_matchea_fila_null_historica`); VentasForm blocks sized-without-variant and submits combos single-line NULL-variant (`ventas-form.spec.ts` VV-1..VV-4 incl. edit mode).

## Commits (5 stacked over `408aeaf` — NOT pushed, NOT PR'd)

Branch chain (stacked-to-main, per delivery decision; current branch `feat/tallas-variantes-xxs-xl-slice2`):

- Slice 1 (backend T1–T6) on `feat/tallas-variantes-xxs-xl-slice1`:
  - `46c4a61` `feat(migrate): seed size variants and add Set Celeno`
  - `27d985a` `fix(migrate): omit size-less sales and NULL-match variants on rerun`
  - `b00a9df` `fix(migrate): align N7 validation with variant semantics`
- Slice 2 (frontend T7–T10) on `feat/tallas-variantes-xxs-xl-slice2` (base `b00a9df`):
  - `b6c0c29` `feat(ventas): add variant-required helpers for sized products`
  - `453a20c` `feat(ventas): require variant for sized products in sale form`

Slice split maps 1:1 to the planned chained PRs (backend PR → frontend PR). No docs commit exists for the openspec artifacts yet — the change folder was untracked at archive time; the orchestrator's delivery step commits the archived artifacts.

## Task Reconciliation

No reconciliation needed: `tasks.md` shows 10/10 implementation tasks (T1–T10) + Phase-6 verification task, all `[x]` at archive time. Task Completion Gate passed as-is.

## Known Pre-existing Conditions (documented, NOT this change's regressions)

1. **4 `test_migrate_stock.py` alias-resolution failures on main** (`assert res["seteados"] == 1` → `assert 0 == 1`): verified identical when checked out at `408aeaf` (the change base). Full-suite exit code is 1; the change-relevant gate uses `-k` filters. Out of scope.
2. **`vue-tsc` not installed/declared** in the frontend: 119 pre-existing type errors, tool-unavailable, NOT gated. Plain `tsc --noEmit` strict passed on the 2 pure-TS touched files; `.vue`-touching files covered by 498 vitest tests (runtime) + clean eslint.
3. **Strict-TDD mode discrepancy** (informational): config `strict_tdd: true` vs apply-progress "Standard mode"; RED→GREEN evidence present regardless.
4. **Slice-1 (T1–T6) safety-net documentation** missing from apply-progress (informational).
5. `--deselect` non-functional on this environment (pytest 8.3.4 + Windows node-ID matching); `-k` filters used instead.

## Rollback Notes

Data-only change — no schema migration (no Alembic). Rollback per proposal: remove Set Celeno + its variants (no FK refs — no BOM/combo wiring yet); re-seed variants by re-running F1 (idempotent); omit+report is policy not persistence — a failed F5 run rolls back per-`session_scope` (EXM-4). Frontend ships independently; the backend 400 guard remains the safety net if the client blocks wrongly. Out-of-scope follow-ups (documented in proposal): Celeno BOM recipe + Caja combo truth-wiring, PRENDAS migration, stock-by-size, per-component combo sizes (`BomProducto.variante_id`).

## Review State

No native review was run for this change yet — PRs are pending (delivery state below). No `reviews/` directory and no `sdd/tallas-variantes-xxs-xl/review/*` Engram topics exist, consistent with the standing unmanaged delivery posture of the prior archived changes. Do NOT start native review from the archive phase.

## Delivery State (PENDING — orchestrator handles PR delivery AFTER archive)

- 5 commits on 2 stacked branches (`feat/tallas-variantes-xxs-xl-slice1` + `feat/tallas-variantes-xxs-xl-slice2`), based on `408aeaf`. **Not pushed, not PR'd.**
- Archive artifacts (archived change folder + spec syncs) are untracked at archive time; the orchestrator's delivery step commits them.
- Planned: 2 chained/stacked PRs (slice1 backend → slice2 frontend) per the stacked-to-main plan. Do NOT push or PR from the archive phase.

## Engram Traceability (observation IDs)

| Artifact | Observation | Sync ID |
|----------|-------------|---------|
| exploration | #497 | obs-76fb5451edd96cc1 |
| proposal | #498 | obs-05466049d5d31855 |
| spec | #499 | obs-8d574809a6d4d3f5 |
| design | #500 | obs-2e6840f4884fe391 |
| tasks | #501 | obs-e9b584effc0c16e5 |
| apply-progress (slices 1+2) | #502 | obs-198e8a931a374969 |
| verify-report | #503 | obs-bce374c4e2fd383a |
| archive-report | topic `sdd/tallas-variantes-xxs-xl/archive-report` | (this report) |

## Follow-ups for Next Phases

- **Delivery (immediate next step)**: orchestrator opens the 2 stacked PRs (slice1 backend → slice2 frontend) and delivers the branch chain. Slice branches must NOT be deleted by the archive phase.
- Later roadmap (out of scope this change): Celeno BOM recipe + Caja combo truth-wiring; canonical size display ordering; per-member combo sizes; stock-by-size.
- Optional hardening suggestions (from verify-report, non-blocking): add `vue-tsc` to devDependencies + typecheck script then fix ~119 pre-existing type errors in a separate change; add a MIG-3 report-content verbatim assertion; record slice-1 safety-net evidence in apply-progress.