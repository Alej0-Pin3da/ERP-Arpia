# Archive Report: compras-wac-ux — Registrar Compra WAC with Live Simulation & History

**Change**: `compras-wac-ux`
**Project**: erp-arpia (`C:/wamp64/www/ERP-Arpia`)
**Status**: CLOSED — archived
**Archived at**: 2026-08-21
**Archived to**: `openspec/changes/archive/2026-08-21-compras-wac-ux/`
**Store**: hybrid (OpenSpec filesystem + Engram mirror `sdd/compras-wac-ux/archive-report`)
**Review gate**: No native review governs this change (no `reviewGate` present in structured status). Unmanaged delivery posture — consistent with prior archived changes. `dependencies.archive: ready` — proceed per SDD archive gate (absence is not a defect when no review was started).
**Cycle**: SDD complete — proposed, speced (2 delta specs), designed, implemented (17/17 tasks across 3 stacked PRs), verified (PASS WITH WARNINGS, 0 blockers), archived.

## Close State

Registrar Compra WAC with Live Simulation & History extends the transactional WAC SSOT (`registrar_compra`, `SELECT FOR UPDATE`, `NUMERIC(15,4)`) with guided UX for **operador** (TOTAL entry + live preview) and **admin/consulta** (history audit). Backend extends `CompraInsumoCreate` with `modo TOTAL|UNIT`, `costo_total`, `factura ≤100`, `proveedor_id?`, and `costo_unitario_aplicado` snapshot; frontend adds TOTAL/UNIT toggle + `computed` parity to 4 decimals, per-row `+ Compra`/`History` wiring, `HistorialDrawer` with `prev→new` WAC running and CSV. Three commits stacked-to-main deliver the full vertical slice; final-state verification confirms 42+578 tests green, built in 4.64s, 11/11 scenarios compliant.

## Final-State Authority

This report is the terminal record at close. Per `sdd-archive` Final-State Authority hierarchy:

1. Structured status `reviewGate` absent — no native receipt to rank (no review started; not a defect).
2. Persisted `tasks.md` — 17/17 `[x]` (Task Completion Gate passed as-is, no reconciliation needed).
3. Explicit final-state facts from the orchestrator launch prompt — authoritative over intermediate snapshots: all warnings reviewed and deemed non-blocking intentional deviations documented in `apply-progress`; no blockers remain; the 3 commits below are the final state at close; no remediation needed. Cited verbatim where snapshot claims would otherwise conflict.
4. `verify-report` and `apply-progress` — intermediate snapshots (lowest rank, valid history only at their write time).

No unrankable contradiction was found: launch prompt's "PASS WITH WARNINGS / no remediation needed / 3 commits final" is corroborated by repository evidence (git log, diff, live test/build re-execution in verify). Snapshot claims are attributed with source/time, not restated as current facts.

## Capabilities Archived

| Capability | Delta Action | Requirements | Scenarios | Verdict |
|------------|--------------|--------------|-----------|---------|
| `compras-insumos` | Updated (2 MODIFIED + 2 ADDED) | REQ-CI-001..004 | SCN-CI-001..006 (6) | PASS |
| `wac-engine` | Updated (2 MODIFIED + 2 ADDED) | REQ-WAC-001..004 | SCN-WAC-001..005 (5) | PASS |
| **Total** |  | **8** | **11** | **11/11 COMPLIANT** |

No REMOVED or RENAMED requirements. Destructive merge guard not triggered.

## Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| `compras-insumos` | Updated | MODIFIED REQ-CI-001 (modo/factura/TOTAL derivation + Infinity guard), MODIFIED REQ-CI-002 (shape adds factura + costo_unitario_aplicado NUMERIC(15,4)), ADDED REQ-CI-003 (History + CSV), ADDED REQ-CI-004 (Inventory view actions); preserved Authorization + List + Decision |
| `wac-engine` | Updated | MODIFIED REQ-WAC-001 (TOTAL price=costo_total/qty before WAC), MODIFIED REQ-WAC-002 (finite guard + display-only rounding), ADDED REQ-WAC-003 (Live preview contract), ADDED REQ-WAC-004 (Atomicity & row locking); preserved Atomic WAC + Row locking base requirements |

### Source of Truth Updated

- `openspec/specs/compras-insumos/spec.md` — merged delta (see table above); now canonical for compras-insumos.
- `openspec/specs/wac-engine/spec.md` — merged delta (see table above); now canonical for wac-engine.

Other capability specs untouched: `bom`, `productos`, `ventas-variantes`, `costos-produccion`, `migracion-catalogos`.

## Commits (3 stacked-to-main, HEAD = 6faf7e4, ahead of origin/main by 3)

- **PR1 45ed755** `feat(compras-wac): backend WAC SSOT with modo TOTAL/UNIT, factura and live preview contract` — schemas/models/migration/service/routes, 356 ins/9 del, 8 files. Backend SSOT authoritative.
- **PR2 fc23fc1** `feat(compras-wac): frontend WAC preview TOTAL/UNIT, historial drawer and CSV` — utils/ComprasForm/HistorialDrawer, 439 ins/82 del, 6 files. Preview + drawer + CSV.
- **PR3 6faf7e4** `feat(compras-wac): wiring InventarioView per-row Compra/History, WAC TOTAL tests and parity` — InventarioView/InsumosTable/tests wiring + parity, 633 ins/52 del, 11 files. Full slice + verification harness.

Range `600691d..6faf7e4` (since `origin/main` 600691d Sprint 1 hardening). Stack strategy: `stacked-to-main`, `auto-chain` per `tasks.md` forecast (High budget risk, 650-750 lines estimated, split <400 per slice).

## Verification Evidence (final-state, outranks stale snapshots)

Final-state facts from the orchestrator launch prompt (authoritative) corroborated by repository evidence:

- **Verdict**: **PASS WITH WARNINGS** — 0 blockers, 0 CRITICAL, schema `gentle-ai.verify-result/v1`, `evidence_revision sha256:0c1346ef4e4911025a6d0b1001aabd151e59a5aa4a814048b584af7b8cc03e3c`, 8/8 requirements / 11/11 scenarios compliant. Warnings reviewed and deemed non-blocking intentional deviations (see below); no remediation needed.
- **Tests**:
  - `pytest backend/tests/test_wac.py + test_compras_insumos.py -q` → **42 passed** (Docker PG 5433, arpia_test isolated DB), includes TOTAL→unit `90/10→9→7.0000`, zero-stock `nuevo==price`, stable `5.0000`, 4 decimals `3.2308`, `commit=False`, concurrent Barrier 2-thread same-insumo `20@7.0000` no lost update + distinct parallel `15@7.6667`.
  - `npm run test` → **64 files 578 passed** (vitest 3.0.5 jsdom, 127s), including `compras-form.spec` + `historial-drawer.spec` parity `10@5+10@9→7.0000` (UNIT and TOTAL), TOTAL toggle recalc, disabled gate `qty0/cost0/Infinity`, CSV header exact.
  - Build `npm run build` → **4.64s 1078 modules** (vite 6.4.3, 153.94 kB chunk, pre-existing warnings only, zero errors).
- **Guards verified**: `Numeric(15,4)` (no FLOAT), `/api/v1` prefix, `SELECT FOR UPDATE` present, finite guards (`isFinite`/`_check_finite` → 422).
- **Spec matrix**: 8 req / 11 scenarios 11/11 COMPLIANT per matrix in `verify-report.md` (REQ-CI-001 SCN-CI-001..003, REQ-CI-002 SCN-CI-004, REQ-CI-003 SCN-CI-005, REQ-CI-004 SCN-CI-006, REQ-WAC-001 SCN-WAC-001/002, REQ-WAC-002 SCN-WAC-003, REQ-WAC-003 SCN-WAC-004, REQ-WAC-004 SCN-WAC-005).
- **Intermediate snapshot attribution**: Per `verify-report` at verification time, build `5.44s` and same test counts (42+578) — later PR3 build `4.64s` is final; delta is timing only, not a regression. No bare present-tense restatement of snapshot timing as current fact.

## Warnings & Suggestions (reviewed — non-blocking; carried forward as notes)

Per `verify-report` at verification time (not current defects per final-state handoff):

- **W1 TDD table formal**: Strict TDD note present but no formal RED/GREEN table in `apply-progress` — tests exist and pass, spirit satisfied → WARNING only.
- **W2 proveedor_id no-FK intentional**: `proveedor_id` without FK (Proveedores removed in 0008) validated via `to_regclass` → 400 — intentional per Design open question, not a defect.
- **W3 nullable costo_unitario_aplicado**: historical rows stay NULL; `Read` as `Decimal|None` slightly diverges from "always string" wording but consistent with migration — intentional.
- **W4 jsdom CSS noise**: `Could not parse CSS stylesheet` from PrimeVue UseStyle — stderr noise, zero failures — harmless.
- **S1** `src/types/api.d.ts` regen via `npm run gen:api` against live backend — deferred, intersection type correct.
- **S2** Add `vitest --coverage` / `pytest --cov` threshold for `ComprasForm.vue`, `HistorialDrawer.vue`, `inventario.ts` — recommended hardening, not a gate (no project coverage gate configured).

Final-state handoff confirms all warnings were reviewed and **no remediation needed** — archive records them as intentional deviations per `apply-progress` Deviations section.

## Task Reconciliation

| Gate | Result |
|------|--------|
| `tasks.md` persisted | 17/17 `[x]` — Phase 1 (1.1-1.3), Phase 2 (2.1-2.4), Phase 3 (3.1-3.3), Phase 4 (4.1-4.4), Phase 5 (5.1-5.3) |
| `apply-progress.md` | 17/17 complete, 3 work-unit commits documented |
| Task Completion Gate | **PASS as-is** — no unchecked implementation tasks; no stale-checkbox reconciliation needed |
| `apply-progress`/`verify-report` proof | Corroborates 17/17 complete; no exceptional repair performed |

Archived `tasks.md` has no unchecked implementation tasks.

## Mechanical Copy Contract

Filesystem operations via shell only; model did not copy bytes via Read→Write for archival move.

- **Spec sync**: Model edit (required for MODIFIED/ADDED merge) — preserved other requirements, maintained heading hierarchy. Spec files validated via direct readback.
- **Archive move**: `cp -R` → snapshot, `git mv` (tracked fallback `mv`), `diff -r` readback.

**Verbatim `diff -r` (source snapshot vs archived tree, archive-report additive-only excluded):**

```
DIFF_EMPTY_PASS
```

Empty diff is the only passing evidence; verbatim output above is the readback. A skipped/missing `diff -r` would have failed the phase — not skipped.

Per-file operation log:

```
snapshotRoot=C:\Users\AstarotH\AppData\Local\Temp\sdd-archive-3a6b4bc3
cp -R openspec/changes/compras-wac-ux → snapshot/source — OK
git mv openspec/changes/compras-wac-ux → openspec/changes/archive/2026-08-21-compras-wac-ux — OK
diff -r snapshot/source ↔ openspec/changes/archive/2026-08-21-compras-wac-ux — DIFF_EMPTY_PASS
```

## Archive Contents

- `proposal.md` ✅
- `specs/compras-insumos/spec.md` ✅ (delta)
- `specs/wac-engine/spec.md` ✅ (delta)
- `specs.md` ✅ (concatenated view)
- `design.md` ✅
- `tasks.md` ✅ (17/17 complete)
- `verify-report.md` ✅ (PASS WITH WARNINGS)
- `archive-report.md` ✅ (this report, additive — excluded from diff)

Active changes directory no longer has this change (`openspec/changes/compras-wac-ux` removed; `openspec/changes/archive/2026-08-21-compras-wac-ux/` is the sole holder).

## Engram Traceability

| Artifact | Source | Key / Path |
|----------|--------|------------|
| proposal | filesystem | `openspec/changes/archive/2026-08-21-compras-wac-ux/proposal.md` |
| specs (delta) | filesystem | `openspec/changes/archive/2026-08-21-compras-wac-ux/specs/compras-insumos/spec.md`, `…/specs/wac-engine/spec.md` |
| design | filesystem | `openspec/changes/archive/2026-08-21-compras-wac-ux/design.md` |
| tasks | filesystem | `openspec/changes/archive/2026-08-21-compras-wac-ux/tasks.md` (17/17) |
| apply-progress | filesystem | `openspec/changes/archive/2026-08-21-compras-wac-ux/apply-progress.md` (tracked but not strictly required for archive move; included in snapshot) |
| verify-report | filesystem | `openspec/changes/archive/2026-08-21-compras-wac-ux/verify-report.md` |
| archive-report | filesystem + Engram | `openspec/changes/archive/2026-08-21-compras-wac-ux/archive-report.md` + Engram topic `sdd/compras-wac-ux/archive-report` (this report, `capture_prompt:false`, `type:architecture`) |

No `engram_mem_search` observation IDs were allocated for this change under the `openspec` artifact store; filesystem paths above are the authoritative audit trail. Engram mirror is the `archive-report` topic only.

## Follow-ups (recorded as notes — NOT blockers)

From `verify-report` suggestions (deferred, not blocking):

- S1: Regen `src/types/api.d.ts` via `npm run gen:api` against live backend so `CompraCreatePayload` intersection becomes native ReqBody.
- S2: Add `vitest --coverage` + `pytest --cov` threshold for WAC-critical files to guard parity regressions.
- Optional: Add formal TDD Cycle Evidence table to `apply-progress` for future strict-TDD audits (W1).

## Rollback Notes

Per `proposal.md` rollback plan: revert migration `20260821_compras_wac_ux.py` + schema/route + `ComprasForm.vue` in a single commit; no data loss. With 3 stacked commits, revert scope is `6faf7e4^..6faf7e4` (PR3) → `fc23fc1` state, or full `45ed755^..6faf7e4` for complete change. Each PR is independently revertable via `git revert`.

## Review State

No native review receipt governs this candidate. Native Review Receipt Gate: `reviewGate` structurally absent — archive proceeds under ordinary repository policy. No `reviewGate present → allow/pending/invalidated` branch was taken; no transaction/ledger/receipt/gate-context topics exist to read.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. Ready for the next change.

---
*Teams responsible: backend `registrar_compra` SSOT + frontend `ComprasForm`/`HistorialDrawer`/`InventarioView`. Contact: maintainer via `openspec/config.yaml` strict_tdd + NUMERIC(15,4) guards.*
