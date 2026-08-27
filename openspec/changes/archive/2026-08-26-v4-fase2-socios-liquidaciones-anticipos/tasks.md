# Tasks: v4-fase2-socios-liquidaciones-anticipos

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900-1100 incl. tests |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 Foundation -> PR2 Core -> PR3 Integration |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Migrations+models | PR1 | `pytest backend/tests/test_migrate_finanzas.py -q` | `alembic upgrade/downgrade && psql \d` | Revert 0011-0013 + models |
| 2 | Schemas+services+API | PR2 | `pytest backend/tests/test_finanzas*.py -q` | `curl /api/v1/finanzas/*` | Revert schemas/services/routes |
| 3 | Frontend adapter+vitest | PR3 | `npm run test -- useSocios useFinanzas` | `VITE_USE_MOCK=false F5 persists` | Revert services/api + composables |

## Phase 1: Foundation (migrations + models)

- [x] 1.1 RED `backend/tests/test_fase2_foundation.py` guards/upgrade/downgrade 0011-0013 (~1h) — Test: `pytest backend/tests/test_fase2_foundation.py -v` 9 passed RED->GREEN — Harness: `alembic downgrade -3 && upgrade head` reversible — Rollback: delete test
- [x] 1.2 GREEN `backend/alembic/versions/0011_extend_socios_configuracion.py` 10 cols+indexes (~1.5h) — Test: `pytest -k socios -q` — Harness: `psql \d Socios_Configuracion` ix_socios_rol/activo — Rollback: downgrade -1
- [x] 1.3 GREEN `backend/alembic/versions/0012_create_liquidaciones.py` header+distribucion CHECKs/FKs (~2h) — Test: `pytest -k liquidacion -q` — Harness: `psql \d liquidaciones` — Rollback: downgrade -1
- [x] 1.4 GREEN `backend/alembic/versions/0013_create_anticipos.py` partial UNIQUE ix_socia_fecha (~1.5h) — Test: `pytest -k anticipo -q` — Harness: `psql \d anticipos` partial UNIQUE — Rollback: downgrade -1
- [x] 1.5 Modify `backend/app/models/finanzas.py` extend Socios + 3 models + 2 StrEnums (~2h) — Test: `pytest test_finanzas.py -q` 58 passed — Harness: `python -c "import app.models.finanzas"` — Rollback: revert file

## Phase 2: Core (schemas + services + api)

- [x] 2.1 RED `backend/tests/test_finanzas_schemas.py` email/tipo_cuenta/monto>0/Literals (~1h) — Test: `pytest test_finanzas_schemas.py -q` — Harness: N/A — Rollback: delete test
- [x] 2.2 GREEN `backend/app/schemas/finanzas.py` Socia/Liquidacion/Anticipo + warnings (~2h) — Test: `pytest test_finanzas_schemas.py -q` — Harness: `py_compile` — Rollback: revert file
- [x] 2.3 RED `backend/tests/test_finanzas_servicios.py` sum105/ fondo_dup/drift>5% (~1.5h) — Test: `pytest test_finanzas_servicios.py -q` — Harness: N/A — Rollback: delete test
- [x] 2.4 GREEN `backend/app/services/finanzas.py` sum-to-100+fondo+drift+FOR UPDATE+FSM (~3h) — Test: `pytest test_finanzas_servicios.py -q` — Harness: `psql sum activo` — Rollback: revert file
- [x] 2.5 RED `backend/tests/test_finanzas_api_v4.py` LIQ code/dup409/FSM422/SET NULL/409 (~2h) — Test: `pytest test_finanzas_api_v4.py -q` — Harness: N/A — Rollback: delete test
- [x] 2.6 GREEN `backend/app/api/routes/finanzas.py` CRUD+PATCH state/descuento paginated (~3h) — Test: `pytest test_finanzas_api_v4.py test_finanzas_api.py -q` — Harness: `curl /api/v1/finanzas/liquidaciones` — Rollback: revert file

## Phase 3: Integration (frontend adapter + vitest + docs)

- [x] 3.1 Create `src/services/api/socios.ts` `liquidaciones.ts` `anticipos.ts` via client (~2h) — Test: `npm run test -- services/api` — Harness: `curl real` — Rollback: delete 3 files
- [x] 3.2 Create `src/composables/useSocios.ts` `useFinanzas.ts` isMock via useMode (~1.5h) — Test: `npm run test -- useSocios` — Harness: `VITE_USE_MOCK true/false` — Rollback: delete 2 files
- [x] 3.3 Vitest `src/composables/useSocios.test.ts` `useFinanzas.test.ts` isMock->atelier vs api (~1.5h) — Test: `npm run test -- useSocios.test` — Harness: N/A jsdom — Rollback: delete tests
- [x] 3.4 Modify `src/stores/atelier.ts` @deprecated + `CambiosV3.md` (~0.5h) — Test: `pytest -q && npm run test -q` — Harness: `F5 persists` — Rollback: revert 2 files
