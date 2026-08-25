# Archive Report: v4-fase1-clientes-ventas

**Change**: v4-fase1-clientes-ventas
**Archived**: 2026-08-24
**Archive location**: openspec/changes/archive/2026-08-24-v4-fase1-clientes-ventas/
**Mode**: hybrid (filesystem + Engram)
**Delivery strategy**: stacked-to-main (3 PRs on main)
**Review budget**: 400 lines — High risk mitigated via stacked slices

## Final-State Authority
Per sdd-archive Final-State Handoff (2026-08-24): Verified PASS 18/18, all tasks 20/20 complete, no blockers. Intermediate apply-progress pre-PR3 pending claims superseded by PR3 commits 7da8c95 + f16e1e1 + 350331e.

## Verdict
PASS — 18/18 scenarios, 9/9 requirements, 0 critical, 0 blockers
Evidence revision: sha256:1a22e5be4d7ff080da05c3f2b97aa323955841c5abd7ba66a9fae156431da031
Verified: 2026-08-24

## Specs Synced
| Domain | Action | Details |
|--------|--------|---------|
| clientes-crm | Created | 3 requirements (CRM-1/CRM-2/CRM-3) — 10 nullable CRM cols + JSONB medidas + tipo/ciudad/q filters |
| ventas-channel-payment | Created | 3 requirements (VCP-1/VCP-2/VCP-3) — metodo_pago + canal 5 enum + frontend adapter |
| sales-master-data | Created | 3 requirements (SMD-1/SMD-2/SMD-3) — 5 canales + 4 metodos seeds + mode reuse |

Source of truth updated:
- openspec/specs/clientes-crm/spec.md
- openspec/specs/ventas-channel-payment/spec.md
- openspec/specs/sales-master-data/spec.md

All 3 were new specs (delta IS full spec). Mechanical copy with temp+diff verification: empty diff PASS for each.

## Archive Contents
- proposal.md present
- design.md present
- specs/clientes-crm/spec.md present
- specs/ventas-channel-payment/spec.md present
- specs/sales-master-data/spec.md present
- tasks.md 20/20 complete
- verify-report.md PASS 18/18
- archive-report.md this file additive

Active changes no longer contains v4-fase1-clientes-ventas — moved to archive.

## Commits on main
- 7da8c95 feat(api): add clientes/ventas/maestros services and useMode with /api/__mode probe
- f16e1e1 feat(frontend): add useClientes/useVentas mock-api adapters and Vitest coverage with @deprecated atelier
- 350331e docs(sdd): finalize tasks 3.1-5.2 and persist proposal/design/verify delta specs (v4-fase1 archive preflight)
All 3 pushed to origin/main at archive time.

## Build and Test Evidence (final)
- pytest 34 passed in 6.01s; 74 passed in 15.98s
- npm run test Vitest 24 passed in 1.10s
- npm run build vite 366 modules in 2.77s
- git diff -- src/**/*.vue empty
- alembic head 0010_ventas_canal_pago on arpia_test:5433 reversible
- CambiosV3.md V3.3.0 exists, atelier.ts @deprecated header present
- TDD 6/6 checks passed

## Mechanical Copy Contract Evidence
- Spec sync: 3x Copy-Item src->temp + Compare-Object empty diff + Move-Item temp->target PASS
- Archive move: Copy-Item snapshot to TEMP/source (8 files) + fallback Move-Item (git mv permission denied) + Get-RelativeMap content diff EMPTY PASS

## Checklist
- [x] Main specs updated correctly
- [x] Change folder moved to archive
- [x] Archive contains all artifacts
- [x] Archived tasks.md has no unchecked tasks (20/20)
- [x] Active changes no longer has this change
- [x] Verbatim diff -r readback included and empty
- [x] No CRITICAL issues (0)
- [x] Commits pushed to origin/main

## SDD Cycle Complete
Ready for next change.
