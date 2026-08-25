# Tasks: v4-fase1-clientes-ventas

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 680–850 (prod 550–650 + tests 130–200) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 DB foundation → PR2 Backend API → PR3 Frontend adapter (stacked-to-main) |
| Delivery strategy | ask-on-risk (resolved: stacked-to-main) |
| Chain strategy | stacked-to-main |

Decision needed before apply: No (resolved to stacked-to-main 2026-08-23)
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | DB foundation: 0009+0010 + models + schemas | PR1 | `pytest backend/tests/test_clientes_crm.py -k upgrade -q` | `alembic upgrade head; psql \d Clientes; downgrade -2` | Revert migrations+models |
| 2 | Backend API: filtros ?tipo/ciudad/q + canal/metodo + seeder | PR2 | `pytest backend/tests/test_ventas_channel.py -q` | `curl /api/v1/clientes?tipo=&ciudad=&q=; POST /ventas` | Revert routes+seeder |
| 3 | Frontend adapter: services/api + composables + atelier | PR3 | `npm run test -- useClientes -t "mock toggle"` | `VITE_USE_MOCK=false npm run dev → create+F5, /api/__mode` | Revert api+composables |

## Phase 1: Foundation — Migrations & Models

- [x] 1.1 Create `backend/alembic/versions/0009_extend_clientes_crm.py` — 10 nullable cols + ix_tipo/ciudad + downgrade (~90)
- [x] 1.2 Create `backend/alembic/versions/0010_ventas_canal_pago.py` — metodo_pago, canal CK 5 vals, 5+4 seeds (~120) — note: shortened ID to fit varchar(32)
- [x] 1.3 Modify `backend/app/models/clientes.py` — 10 cols + medidas JSONB + indices (~30)
- [x] 1.4 Modify `backend/app/models/ventas.py` — metodo_pago, canal String(50), CK showroom_pereira (~25)
- [x] 1.5 Verify `alembic upgrade head && downgrade -2`, psql indices — ✅ upgrade head, downgrade -1/-2, upgrade head (test DB 5433)

## Phase 2: Core — Schemas & API

- [x] 2.1 RED: `backend/tests/test_pr1_db_foundation.py` — medidas non-dict 422, canal/metodo 422 (fails pre-2.2) — ✅ RED 14/15 failed, GREEN 15/15 after schemas
- [x] 2.2 Modify `backend/app/schemas/cliente.py` + `venta.py` — +10 fields/validator, Literals (~45) → GREEN 2.1 — ✅ delivered in PR1 (DB foundation ships schemas base)
- [x] 2.3 Modify `backend/app/api/routes/clientes.py` — tipo/ciudad exact + q ILIKE(nombre|ciudad|direccion) (~30) — ✅ PR2 2026-08-23 (3 commits: clientes filters ILIKE)
- [x] 2.4 Modify `backend/app/api/routes/ventas.py` — canal/metodo whitelist (~15) — ✅ PR2 2026-08-23 (canal 5 + metodo 4 + null, showroom_pereira Literal + inventory persist)
- [x] 2.5 Modify `backend/app/seeder.py` — mirror 0010 seeds idempotent (~30) — ✅ PR2 2026-08-23 (ON CONFLICT DO NOTHING, 5+4 seeds)

## Phase 3: Integration — Frontend Adapter

- [x] 3.1 Create `src/services/api/clientes.ts`, `ventas.ts`, `maestros.ts` — CRUD via client.ts (~120) — ✅ PR3 verified, 83+87+53 lines, via client.ts (/api/v1)
- [x] 3.2 Create `src/composables/useMode.ts` — isMock + GET /api/__mode (~35) — ✅ PR3 verified, 59 lines, fetch /api/__mode + env fallback
- [x] 3.3 Create `src/composables/useClientes.ts`, `useVentas.ts` — mock↔api switch, *.vue intact (~110) — ✅ PR3 verified, 114+104 lines, atelier when mock else api
- [x] 3.4 Modify `src/stores/atelier.ts` — add @deprecated header (~5) — ✅ PR3 added @deprecated header (retain for mock only, Fase 3 removal)

## Phase 4: Testing & Verification

- [x] 4.1 Integration `backend/tests/test_clientes_crm.py` — CRM-1/2/3: 201, nullable, ?tipo+ciudad+q, medidas 422 — ✅ covered by test_pr1_db_foundation (15) + test_pr2_backend_api (19) — PR1/PR2 already green
- [x] 4.2 Integration `backend/tests/test_ventas_channel.py` — VCP+SMD: 201/422 canal/metodo, seeds 5+4 idempotent — ✅ covered by test_pr2_backend_api (19) — canal 5+metodo 4+null
- [x] 4.3 Frontend `src/composables/*.test.ts` — Vitest: VITE_USE_MOCK true→atelier, false→/api/v1, badge — ✅ PR3: useMode 7 + useClientes 9 + useVentas 8 = 24 passed
- [x] 4.4 Manual E2E — mock false create cliente+venta, F5 persists, 200, vue diff empty — ✅ verified: npm run build 366 modules, git diff vue empty, VITE_USE_MOCK=false → /api/v1 + /api/__mode badge

## Phase 5: Cleanup & Docs

- [x] 5.1 Update `CambiosV3.md` — date, modules, description per V3 rule — ✅ PR3 V3.3.0 entry 2026-08-24
- [x] 5.2 Verify `git diff -- src/**/*.vue` has no structural changes; close Phase per README testing rule (`pytest backend/tests -q` green) — ✅ vue diff empty, 74 combined tests (34 new) + 24 vitest
