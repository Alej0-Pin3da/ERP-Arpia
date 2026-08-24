# Apply Progress: v4-fase1-clientes-ventas — PR1 (DB foundation)

**Change**: v4-fase1-clientes-ventas
**PR**: PR1 — DB foundation (stacked-to-main, slice 1/3)
**Mode**: Strict TDD
**Scope**: Phase 1 (1.1–1.5) + Schemas base (2.1–2.2) — DB-only, no frontend, no API filters
**Updated**: 2026-08-23
**Chain strategy**: stacked-to-main (resolved from ask-on-risk)

## Completed Tasks

- [x] 1.1 Create `backend/alembic/versions/0009_extend_clientes_crm.py` — 10 nullable cols + ix_tipo/ciudad + downgrade
- [x] 1.2 Create `backend/alembic/versions/0010_ventas_canal_pago.py` — metodo_pago, canal CK 5 vals, 5+4 seeds (shortened ID to fit varchar(32))
- [x] 1.3 Modify `backend/app/models/clientes.py` — 10 cols + medidas JSONB + indices
- [x] 1.4 Modify `backend/app/models/ventas.py` — metodo_pago, canal String(50), CK showroom_pereira
- [x] 1.5 Verify `alembic upgrade head && downgrade -2`, psql indices — ✅ head → 0010_ventas_canal_pago, downgrade -1/-2, upgrade head
- [x] 2.1 RED: medidas non-dict 422, canal/metodo 422 — via `backend/tests/test_pr1_db_foundation.py`
- [x] 2.2 Modify `backend/app/schemas/cliente.py` + `venta.py` — +10 fields/validator, Literals → GREEN 2.1

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

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | Triangulate | Refactor |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.3 | `backend/tests/test_pr1_db_foundation.py` | Unit+Integration | ✅ 593 passed / 12 pre-existing failed (baseline 2026-08-23) | ✅ 3 cases failed (missing cols/indices) | ✅ Passed 3/3 after model | ✅ 2+ paths (medidas JSONB type, indices) | ✅ Index explicit naming |
| 1.4 | `backend/tests/test_pr1_db_foundation.py` | Unit | ✅ same baseline | ✅ 3 cases failed (metodo_pago, varchar 50, CK) | ✅ Passed 3/3 after model | ✅ 2 cases (CK 5 vs 4, widen) | ✅ None needed |
| 2.2 | `backend/tests/test_pr1_db_foundation.py` | Unit | ✅ same baseline | ✅ 11/15 failed (medidas, canal showroom, metodo) | ✅ 15/15 after schemas | ✅ 3 cases (valid dict + non-dict 422 + None; valid canal/metodo + invalid 422 + null) | ✅ Validator extraction |

### Test Summary

- **Total tests written**: 15 in `backend/tests/test_pr1_db_foundation.py`
- **Total tests passing**: 15/15 (100%)
- **Layers used**: Unit (15), Integration (0 — model/table inspection, no DB round-trip), E2E (0)
- **Approval tests** (refactoring): 0 — no refactoring, greenfield extension
- **Pure functions created**: 1 validator (`validate_medidas` on ClienteBase/Update)

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `pytest backend/tests/test_pr1_db_foundation.py -q` → **15 passed in 0.98s** (after GREEN); RED run was 14 failed 1 passed |
| Runtime harness command/scenario and exact result | `DATABASE_URL=...5433/arpia_test alembic upgrade head` → **head at 0010_ventas_canal_pago** <br> `alembic downgrade -1` → 0009 <br> `alembic upgrade head` → head <br> `alembic downgrade -2` → 20260821_wac <br> `alembic upgrade head` → head <br> `psql \d Clientes` → ix_clientes_tipo/ciudad present, 10 cols nullable, medidas jsonb <br> `select * from maestros_*` → 5 canales, 4 metodos, idempotent on re-run |
| Rollback boundary | Revert `backend/alembic/versions/0009*`, `0010*`, `backend/app/models/clientes.py`, `ventas.py`, `schemas/cliente.py`, `venta.py`, `backend/tests/test_pr1_db_foundation.py` — no API route or frontend touched; `alembic downgrade -2` restores pre-PR1 schema without data loss (nullable cols) |

## Deviations from Design

- **Revision ID shortened**: Design names `0010_fix_ventas_canal_y_metodo_pago` (35 chars) exceeds `alembic_version.version_num VARCHAR(32)`; implemented as `0010_ventas_canal_pago` (22 chars). Behavior identical; downgrade path references new ID. Noted in tasks.md 1.2.
- **Schemas base delivered in PR1**: Design/tasks split schemas into Phase 2 (2.2), but PR1 DB foundation per delivery instruction ships models+schemas base together to keep PR1 autonomous and testable via RED→GREEN without API. Remaining Phase 2 tasks (2.3–2.5 routes+seeder) stay for PR2.
- **Maestros models not created**: Tables `maestros_canales_venta`/`maestros_metodos_pago` are created via Alembic directly (phase ships VARCHAR whitelist, FK deferred). No SQLAlchemy model needed for PR1; PR2 may add read-only models if API needs them.

## Issues Found

- **Pre-existing test failures (12/605)**: Baseline `pytest backend/tests -q` shows 12 failures unrelated to PR1 (email .local validation in test_clientes/test_audit, migrante sales counts, devolver pagination). All 593 passed tests remain passing; PR1 adds 15 new passing tests.
- **Legacy Alembic CK ordering**: Existing migration `98bda77bcd4d` updates estado before dropping CK, fails on non-empty dev DB (arpia:5432). On empty test DB (arpia_test:5433) via `_recrear_bd_test` it passes. PR1 migrations use correct order (drop CK then create new).
- **Legacy channel values**: Design lists `Feria Showroom`, `WhatsApp / DM`, `Showroom Pereira` mappings — implemented as direct UPDATEs plus LOWER catch for `showroom`.

## Remaining Tasks

- [ ] 2.3 Modify `backend/app/api/routes/clientes.py` — tipo/ciudad exact + q ILIKE(nombre|ciudad|direccion)
- [ ] 2.4 Modify `backend/app/api/routes/ventas.py` — canal/metodo whitelist
- [ ] 2.5 Modify `backend/app/seeder.py` — mirror 0010 seeds idempotent
- [ ] 3.1 Create `src/services/api/clientes.ts`, `ventas.ts`, `maestros.ts`
- [ ] 3.2 Create `src/composables/useMode.ts`
- [ ] 3.3 Create `src/composables/useClientes.ts`, `useVentas.ts`
- [ ] 3.4 Modify `src/stores/atelier.ts` — @deprecated header
- [ ] 4.1–4.4 Integration, frontend Vitest, manual E2E
- [ ] 5.1 CambiosV3.md, 5.2 git diff -- src/**/*.vue

## Workload / PR Boundary

- Mode: stacked PR slice
- Current work unit: PR1 DB foundation
- Boundary: Starts after `20260821_wac` (head pre-PR1); ends at `0010_ventas_canal_pago` inclusive; includes models+schemas base for autonomous RED→GREEN without touching routes/frontend
- Estimated review budget impact: ~265 lines prod (90+120+30+25) +45 schemas +30 tests = ~340 lines authored, under 400 budget for this slice

## Verification Performed

- `pytest backend/tests/test_pr1_db_foundation.py -q` → 15 passed
- `pytest backend/tests/test_clientes.py` — GET consulta 200 still validated (aside from pre-existing email .local issue)
- `alembic upgrade head` → 0010_ventas_canal_pago (head) on arpia_test:5433
- `alembic downgrade -1 && upgrade head` → reversible
- `alembic downgrade -2 && upgrade head` → reversible, indices and seeds restored
- `psql \d` via sqlalchemy inspect → indices ix_clientes_tipo/ciudad present, CHECK showroom_pereira present, canal VARCHAR(50)

## Next Recommended

- sdd-apply PR2 (Phase 2: Core — filters + canal/metodo route validation + seeder mirror) — stacked onto PR1 branch `feat/v4-fase1-clientes-ventas-pr1` targeting `main`; PR2 branch will target PR1 branch.
- Alternatively sdd-verify for PR1 slice isolation (focused verify of DB foundation).

## Risks

- Seed idempotency relies on ON CONFLICT (codigo); if maestros tables gain FK in Fase 3, downgrade drop-table logic will need to guard against non-empty manual rows.
- `showroom_pereira` canonical key pending business confirm (design open question) — kept as underscore form; FE dropdown must match.
