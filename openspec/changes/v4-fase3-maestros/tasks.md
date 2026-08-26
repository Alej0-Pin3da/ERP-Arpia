# Tasks: v4-fase3-maestros

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900-1000 incl tests |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 0014 -> PR2 0015+frontend |
| Delivery strategy | stacked-to-main |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | 0014: proveedores+categoria+ubicacion+extend stubs+models | PR1 | `pytest backend/tests/test_maestros_proveedores.py -q` | `alembic upgrade head && psql \d maestros_proveedores` | Revert `0014_*.py`+`maestros.py`; `downgrade -1` |
| 2 | 0015+API+frontend: tallas+sin-talla+parametros+schemas/API+maestros.ts/useMaestros+vitest | PR2 | `pytest backend/tests -k maestros -q && npm run test -- useMaestros` | `curl /maestros/tallas-estandar?sort_by=orden && VITE_USE_MOCK=false F5` | Revert `0015_*.py`+`schemas/services/routes`+`maestros.ts/useMaestros.ts`; `downgrade -1` |

## Phase 1: Foundation

- [x] 1.1 RED `backend/tests/test_maestros_guards.py` `_has_table/_has_column` 0014 — Test: `pytest backend/tests/test_maestros_guards.py -q` — Harness: `alembic check` — Rollback: delete test
- [x] 1.2 `backend/alembic/versions/0014_maestros_core.py` 3 CREATE+2 ALTER `_has_*`+ON CONFLICT — Test: `alembic upgrade head && pytest backend/tests/test_maestros_guards.py -q` — Harness: `psql \d maestros_canales_venta` — Rollback: `downgrade -1`
- [x] 1.3 `backend/app/models/maestros.py` 8 models CHECK/UNIQUE/15,4/TIMESTAMPTZ + `__init__.py` — Test: `pytest backend/tests/test_maestros_models.py -q` — Harness: `python -c "from app.models.maestros import ProveedorMaestro"` — Rollback: revert 2 files

## Phase 2: Core

- [ ] 2.1 RED `backend/tests/test_maestros_proveedores.py` MP-1 201/409/422+q/categoria+Paginated — Test: `pytest backend/tests/test_maestros_proveedores.py -q` — Harness: `curl /maestros/proveedores?q=atenea` — Rollback: delete test
- [ ] 2.2 GREEN `backend/app/schemas/maestros.py` ProveedorCreate/Read + `services/maestros.py` + `api/routes/maestros.py` proveedores — Test: `pytest backend/tests/test_maestros_proveedores.py -q` — Harness: `curl -X POST /maestros/proveedores` — Rollback: revert 3 files
- [ ] 2.3 RED+GREEN `backend/tests/test_maestros_categorias_ubicaciones.py` + routes MCU-1/2 `tipo_talla`3/`tipo`4/`UB-*` — Test: `pytest backend/tests/test_maestros_categorias_ubicaciones.py -q` — Harness: `curl /maestros/ubicaciones-taller?tipo=ROLLOS_TELAS` — Rollback: revert slice
- [ ] 2.4 RED+GREEN `backend/tests/test_maestros_ventas_extend.py` VCP-1/2 metodo_pago null+canal 5-enum — Test: `pytest backend/tests/test_maestros_ventas_extend.py -q` — Harness: `alembic downgrade -1 && upgrade head` — Rollback: revert slice
- [ ] 2.5 RED+GREEN `backend/tests/test_maestros_tallas.py` MT-1/MPS-1 orden UNIQUE+precio ge0 — Test: `pytest backend/tests/test_maestros_tallas.py -q` — Harness: `curl /maestros/tallas-estandar?sort_by=orden` — Rollback: delete routes
- [ ] 2.6 RED+GREEN `backend/tests/test_maestros_parametros.py` MPC-1/2 singleton auto-create+sum100 FOR UPDATE+race — Test: `pytest backend/tests/test_maestros_parametros.py -q` — Harness: `curl PATCH /maestros/parametros-costeo` 2x — Rollback: revert singleton
- [ ] 2.7 `backend/alembic/versions/0015_maestros_tallas.py` CREATE tallas+sin-talla+parametros 40/30/30 + `seeder.py` — Test: `alembic upgrade head && pytest backend/tests -k maestros -q` — Harness: `psql select * from maestros_parametros_costeo` — Rollback: `downgrade -1`

## Phase 3: Wiring

- [ ] 3.1 `src/services/api/maestros.ts` 53->250 8 clients Paginated+tryFetch — Test: `npm run test -- maestros` — Harness: `curl /maestros/proveedores` — Rollback: revert `maestros.ts`
- [ ] 3.2 `src/composables/useMaestros.ts` `isMock?atelier:api` 8 groups+singleton — Test: `npm run test -- useMaestros` — Harness: `VITE_USE_MOCK=false GET /maestros/...` — Rollback: delete file
- [ ] 3.3 `src/views/MaestrosView.vue` wire `guardar*/eliminar*` keeps 7 tabs+F5 — Test: `npm run test -- MaestrosView` — Harness: `VITE_USE_MOCK=false create->F5` — Rollback: revert vue
- [ ] 3.4 `src/composables/useMaestros.test.ts` Vitest isMock+fallback + `CambiosV3.md`+`main.py` — Test: `npm run test -- useMaestros && pytest backend/tests -q` — Harness: `pytest -q && npm run test` — Rollback: revert 3 files
