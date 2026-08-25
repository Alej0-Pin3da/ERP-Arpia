# Apply Progress: v4-fase1-clientes-ventas — PR1 (DB foundation) + PR2 (Backend API)

**Change**: v4-fase1-clientes-ventas
**PR**: PR1 DB foundation (slice 1/3) + **PR2 Backend API (slice 2/3)** — stacked-to-main
**Mode**: Strict TDD
**Scope**: Phase 1 (1.1–1.5) + Schemas base (2.1–2.2) + **Phase 2 Backend API (2.3–2.5)**
**Updated**: 2026-08-23 (PR1) / 2026-08-24 (PR2)
**Chain strategy**: stacked-to-main (resolved from ask-on-risk)
**Review budget**: PR1 ~340 lines, PR2 ~86 prod + 488 test lines (3 commits, each <400)

## Completed Tasks

- [x] 1.1 Create `backend/alembic/versions/0009_extend_clientes_crm.py` — 10 nullable cols + ix_tipo/ciudad + downgrade
- [x] 1.2 Create `backend/alembic/versions/0010_ventas_canal_pago.py` — metodo_pago, canal CK 5 vals, 5+4 seeds (shortened ID to fit varchar(32))
- [x] 1.3 Modify `backend/app/models/clientes.py` — 10 cols + medidas JSONB + indices
- [x] 1.4 Modify `backend/app/models/ventas.py` — metodo_pago, canal String(50), CK showroom_pereira
- [x] 1.5 Verify `alembic upgrade head && downgrade -2`, psql indices — ✅ head → 0010_ventas_canal_pago, downgrade -1/-2, upgrade head
- [x] 2.1 RED: medidas non-dict 422, canal/metodo 422 — via `backend/tests/test_pr1_db_foundation.py`
- [x] 2.2 Modify `backend/app/schemas/cliente.py` + `venta.py` — +10 fields/validator, Literals → GREEN 2.1
- [x] 2.3 Modify `backend/app/api/routes/clientes.py` — tipo/ciudad exact + q ILIKE(nombre|ciudad|direccion) combinable, paginado — ✅ PR2 2026-08-24
- [x] 2.4 Modify `backend/app/api/routes/ventas.py` + `backend/app/services/inventory.py` — canal 5 valores (Literal incluye showroom_pereira) + metodo_pago 4 + null (422 si inválido), persist metodo_pago — ✅ PR2 2026-08-24
- [x] 2.5 Modify `backend/app/seeder.py` — mirror 0010 seeds idempotent ON CONFLICT DO NOTHING (5 canales + 4 metodos) — ✅ PR2 2026-08-24

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/alembic/versions/0009_extend_clientes_crm.py` | Created | 10 nullable cols (ciudad 80, direccion 200, tipo 30, tallas 10, categoria_preferida 50, tipo_producto_frecuente 50, notas TEXT, medidas JSONB) + ix_clientes_tipo/ciudad, idempotent guards, downgrade drops indices/cols |
| `backend/alembic/versions/0010_ventas_canal_pago.py` | Created | metodo_pago VARCHAR(50) nullable, canal VARCHAR(50) widen, CK 5 valores (web|whatsapp|instagram|feria|showroom_pereira), legacy mapping (Feria Showroom→feria etc.), maestros_canales_venta + maestros_metodos_pago tables + 5+4 ON CONFLICT DO NOTHING seeds |
| `backend/app/models/clientes.py` | Modified | +10 cols + Index ix_clientes_tipo/ciudad, JSONB medidas |
| `backend/app/models/ventas.py` | Modified | canal_venta String(50), metodo_pago String(50) nullable, CK showroom_pereira |
| `backend/app/schemas/cliente.py` | Modified | ClienteBase + ClienteUpdate +10 fields + medidas dict validator (422 on non-dict) |
| `backend/app/schemas/venta.py` | Modified | VentaCreate canal Literal + showroom_pereira, metodo_pago Literal 4 + None, VentaRead + metodo_pago |
| `backend/tests/test_pr1_db_foundation.py` | Created | 15 tests: Cliente/Venta model existence, indices, CK, schema validation (Strict TDD RED→GREEN) |
| `backend/app/api/routes/clientes.py` | Modified (PR2) | Added tipo/ciudad exact filters + q ILIKE(nombre|ciudad|direccion) combinable, paginated |
| `backend/app/api/routes/ventas.py` | Modified (PR2) | Expanded Literal canal_venta to include showroom_pereira (5 values) |
| `backend/app/services/inventory.py` | Modified (PR2) | Persist metodo_pago in registrar_venta and actualizar_venta |
| `backend/app/seeder.py` | Modified (PR2) | Added CANALES_VENTA/METODOS_PAGO constants + seed_canales_venta/seed_metodos_pago idempotent + wired into run() |
| `backend/tests/test_pr2_backend_api.py` | Created (PR2) | 19 tests: clientes filters (tipo/ciudad/q ILIKE combinable + paginated), ventas whitelist (canal 5 + metodo 4 + null 422), seeder mirror idempotent |

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | Triangulate | Refactor |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.3 | `backend/tests/test_pr1_db_foundation.py` | Unit+Integration | ✅ 593 passed / 12 pre-existing failed (baseline 2026-08-23) | ✅ 3 cases failed (missing cols/indices) | ✅ Passed 3/3 after model | ✅ 2+ paths (medidas JSONB type, indices) | ✅ Index explicit naming |
| 1.4 | `backend/tests/test_pr1_db_foundation.py` | Unit | ✅ same baseline | ✅ 3 cases failed (metodo_pago, varchar 50, CK) | ✅ Passed 3/3 after model | ✅ 2 cases (CK 5 vs 4, widen) | ✅ None needed |
| 2.2 | `backend/tests/test_pr1_db_foundation.py` | Unit | ✅ same baseline | ✅ 11/15 failed (medidas, canal showroom, metodo) | ✅ 15/15 after schemas | ✅ 3 cases (valid dict + non-dict 422 + None; valid canal/metodo + invalid 422 + null) | ✅ Validator extraction |
| 2.3 | `backend/tests/test_pr2_backend_api.py` | Integration | ✅ 23 passed (test_pr1 + test_clientes) | ✅ ImportError before clientes filters (q/tipo/ciudad missing) + parametrized filter cases failed | ✅ 4/4 passed after clientes.py filters | ✅ 3 cases (tipo exact + ciudad exact + combinable q tipo/ciudad + paginated) + case-insensitive ILIKE | ✅ or_ extraction, like var reuse |
| 2.4 | `backend/tests/test_pr2_backend_api.py` | Integration | ✅ same 23 baseline | ✅ Invalid canal 422 failed (showroom_pereira missing in Literal), metodo_pago not persisted | ✅ 12/12 passed after ventas.py Literal + inventory metodo_pago | ✅ 5 canales + 4 metodos + invalid 422 + null + list filter showroom | ✅ None needed |
| 2.5 | `backend/tests/test_pr2_backend_api.py` | Integration | ✅ same baseline | ✅ ImportError seed_canales_venta before seeder | ✅ 2/2 passed after seeder mirror | ✅ 5 canales + 4 metodos + idempotent double-run | ✅ ON CONFLICT DO NOTHING + CREATE TABLE IF NOT EXISTS guard |

### Test Summary

- **Total tests written**: 15 in `backend/tests/test_pr1_db_foundation.py` + **19 in `backend/tests/test_pr2_backend_api.py` = 34 new**
- **Total tests passing**: PR1 15/15 + PR2 19/19 = **34/34 (100%)** for new tests; full suite `test_pr1 + test_clientes + test_ventas_api + test_pr2` → **74 passed**
- **Layers used**: Unit (15), Integration (19), E2E (0)
- **Approval tests** (refactoring): 0 — no refactoring, greenfield extension
- **Pure functions created**: 1 validator (`validate_medidas`) + 2 seed helpers (`seed_canales_venta`, `seed_metodos_pago`)

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | PR1: `pytest backend/tests/test_pr1_db_foundation.py -q` → **15 passed in 0.98s** (after GREEN); RED was 14 failed 1 passed <br> **PR2: `pytest backend/tests/test_pr2_backend_api.py -q` → 19 passed in 5.72s** (after GREEN); RED was ImportError seed_canales_venta + filter failures <br> **Combined: `pytest backend/tests/test_pr1_db_foundation.py backend/tests/test_clientes.py backend/tests/test_ventas_api.py backend/tests/test_pr2_backend_api.py -q` → 74 passed in 15.87s** |
| Runtime harness command/scenario and exact result | PR1: `alembic upgrade head` → **head at 0010_ventas_canal_pago** on arpia_test:5433; downgrade -1/-2 reversible <br> **PR2: `SELECT version_num FROM alembic_version` on arpia_test → 0010_ventas_canal_pago (still head)** <br> PR2: `GET /clientes?tipo=mayorista&ciudad=Pereira&q=maria` → combinable filter 200, pagination limit/offset honored <br> PR2: `POST /ventas {canal:showroom_pereira, metodo_pago:transferencia}` → 201, `POST /ventas {canal:telefono}` → 422, `POST /ventas {metodo:cripto}` → 422, null metodo → 201 <br> PR2: `seed_canales_venta` + `seed_metodos_pago` double-run → 5 canales + 4 metodos, idempotent <br> PR2: `npm run build` → ✅ vite build 366 modules, dist built |
| Rollback boundary | PR1: Revert `backend/alembic/versions/0009*`, `0010*`, `backend/app/models/clientes.py`, `ventas.py`, `schemas/cliente.py`, `venta.py`, `backend/tests/test_pr1_db_foundation.py` <br> **PR2: Revert `backend/app/api/routes/clientes.py`, `ventas.py`, `backend/app/services/inventory.py`, `backend/app/seeder.py`, `backend/tests/test_pr2_backend_api.py` — PR2 alone is reversible without touching PR1 migrations/models. Combined rollback = PR1+PR2 above + `alembic downgrade -2` restores pre-PR1 schema.** |

## Deviations from Design

- **Revision ID shortened**: Design names `0010_fix_ventas_canal_y_metodo_pago` (35 chars) exceeds `alembic_version.version_num VARCHAR(32)`; implemented as `0010_ventas_canal_pago` (22 chars). Behavior identical; downgrade path references new ID. Noted in tasks.md 1.2.
- **Schemas base delivered in PR1**: Design/tasks split schemas into Phase 2 (2.2), but PR1 DB foundation per delivery instruction ships models+schemas base together to keep PR1 autonomous and testable via RED→GREEN without API. Remaining Phase 2 tasks (2.3–2.5 routes+seeder) delivered in PR2 as planned.
- **Maestros models not created**: Tables `maestros_canales_venta`/`maestros_metodos_pago` are created via Alembic directly (phase ships VARCHAR whitelist, FK deferred). No SQLAlchemy model needed for PR1/PR2; seeder mirror uses raw SQL with ON CONFLICT.
- **Clientes q ILIKE superset**: Spec says q ILIKE on nombre|ciudad|direccion; PR2 implements exactly that (removes documento/email/telefono from earlier PR1-era filter which was pre-spec). Kept combinable exact tipo/ciudad + q as specified. If telefono/email search is needed later, additive without breaking spec.

## Issues Found

- **Pre-existing test failures (12/605)**: Baseline `pytest backend/tests -q` shows 12 failures unrelated to PR1/PR2 (email .local validation, migrante sales counts, etc.). All 593 passed tests remain passing; PR1+PR2 add 34 new passing tests; combined focused 74 tests green.
- **Legacy Alembic CK ordering**: Migration `98bda77bcd4d` fails on non-empty dev DB (arpia:5432) due to estado update before CK drop. On empty test DB (arpia_test:5433) via `_recrear_bd_test` it passes. Both PR1/PR2 migrations use correct order (drop CK then create new).
- **Legacy channel values**: `Feria Showroom`, `WhatsApp / DM`, `Showroom Pereira` mappings implemented in 0010 upgrade.

## Remaining Tasks

- [ ] 3.1 Create `src/services/api/clientes.ts`, `ventas.ts`, `maestros.ts`
- [ ] 3.2 Create `src/composables/useMode.ts`
- [ ] 3.3 Create `src/composables/useClientes.ts`, `useVentas.ts`
- [ ] 3.4 Modify `src/stores/atelier.ts` — @deprecated header
- [ ] 4.1–4.4 Integration, frontend Vitest, manual E2E
- [ ] 5.1 CambiosV3.md, 5.2 git diff -- src/**/*.vue

## Workload / PR Boundary

- Mode: stacked PR slice
- Current work unit: **PR2 Backend API (2.3–2.5) — 3 atomic commits**
  - Commit 941acee `feat(api): add clientes filters ...` — 1 file, ~10 lines
  - Commit c096947 `feat(api): expand ventas canal ...` — 2 files, ~5 lines
  - Commit f7b8e23 `feat(seeder): mirror Alembic 0010 ...` — 2 files, ~488 lines (mostly tests)
- Boundary: Starts after PR1 head `0010_ventas_canal_pago` (no new migrations in PR2); ends with routes+seeder+inventory wired; no frontend touched.
- Estimated review budget impact: PR2 prod ~86 lines (clientes 10 + ventas 2 + inventory 4 + seeder 70) + tests 488 lines; prod under 400, total authored ~574 but tests excluded from authored risk per SDD guard.
- Chain: stacked-to-main — PR1 and PR2 both on main sequentially; PR3 will target main after PR2.

## Verification Performed

- `pytest backend/tests/test_pr1_db_foundation.py -q` → 15 passed (PR1 still green)
- `pytest backend/tests/test_pr2_backend_api.py -q` → 19 passed (PR2 GREEN; RED was ImportError before seeder)
- `pytest backend/tests/test_pr1_db_foundation.py backend/tests/test_clientes.py backend/tests/test_ventas_api.py backend/tests/test_pr2_backend_api.py -q` → **74 passed in 15.87s**
- `pytest backend/tests/test_pr1_db_foundation.py backend/tests/test_clientes.py -q` safety net before PR2 → 23 passed
- `SELECT version_num FROM alembic_version` on arpia_test:5433 → **0010_ventas_canal_pago (still head, PR2 adds no migration)**
- `SELECT codigo FROM maestros_canales_venta / maestros_metodos_pago` double-run → 5 + 4, idempotent
- `npm run build` → ✅ vite build 366 modules, dist built (PR2 no frontend change)
- `POST /ventas {canal_venta:showroom_pereira}` 201 + `GET /ventas?canal_venta=showroom_pereira` 200 filter works
- `POST /ventas {metodo_pago:cripto}` 422, `canal:telefono` 422

## Next Recommended

- **sdd-apply PR3 (Phase 3 Frontend adapter)** — `src/services/api/clientes.ts`, `ventas.ts`, `maestros.ts` + `composables/useMode|useClientes|useVentas` + `atelier.ts @deprecated`. Depends on PR2 backend being live; verify with `VITE_USE_MOCK=false` against real `/api/v1` and `GET /api/__mode` badge. Estimated ~270 lines prod.
- Alternatively: sdd-verify for PR1+PR2 combined slice if verification gate before PR3.

## Risks

- PR2's clientes q filter now searches only nombre|ciudad|direccion (spec). If existing callers relied on q searching documento/email/telefono, that path is now narrower — but no existing test covers that exact legacy q behavior beyond nombre; the 12 pre-existing failures are unrelated.
- Seed idempotency relies on ON CONFLICT (codigo); if maestros tables gain FK in Fase 3, downgrade drop-table logic will need to guard against non-empty manual rows.
- `showroom_pereira` canonical key pending business confirm — kept as underscore form; FE dropdown must match. Validate in PR3.
