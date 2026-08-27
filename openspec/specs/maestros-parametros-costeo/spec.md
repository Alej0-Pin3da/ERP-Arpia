# Delta for maestros-parametros-costeo

## ADDED Requirements

### Requirement: MPC-1: ParametrosCosteo Singleton Read

The system MUST persist singleton `maestros_parametros_costeo` row `id=1` with fields: `costo_minuto_costura NUMERIC(15,4) ge=0`, `costo_hora_patronaje NUMERIC(15,4) ge=0`, `margen_meta_global_pct NUMERIC(15,4) ge=0 le=100`, `desperdicio_textil_default_pct NUMERIC(15,4) ge=0 le=100`, `iva_regimen_pct NUMERIC(15,4) ge=0 le=100`, `distribucion_reinversion_pct/reparto_margara_pct/reparto_valqui_pct` each `ge=0 le=100`. `GET /api/v1/maestros/parametros-costeo` MUST return singleton; if not seeded, MUST auto-create default. `POST`/`DELETE` MUST NOT exist (405).

#### Scenario: Get singleton

- GIVEN singleton seeded with `distribucion 40/30/30`
- WHEN `GET /maestros/parametros-costeo` is called
- THEN 200 and `distribucion_reinversion_pct` is 40

#### Scenario: Auto-create on first GET

- GIVEN singleton row absent (fresh DB before seed)
- WHEN `GET /maestros/parametros-costeo` is called
- THEN 200 with defaults and row is created

### Requirement: MPC-2: ParametrosCosteo Patch Guard

The system MUST allow `PATCH /maestros/parametros-costeo` with partial body and MUST validate `distribucion_reinversion_pct + reparto_margara_pct + reparto_valqui_pct == 100` else 422. Service MUST use `SELECT ... FOR UPDATE` on `id=1` to serialize concurrent patches. Valid patch MUST persist and return 200.

#### Scenario: Valid sum persists

- GIVEN `PATCH /maestros/parametros-costeo` with `{"distribucion_reinversion_pct":40,"reparto_margara_pct":30,"reparto_valqui_pct":30,"costo_minuto_costura":120.5}`
- WHEN processed
- THEN 200 and subsequent `GET` reflects new values

#### Scenario: Invalid sum rejected

- GIVEN `PATCH` with `{"distribucion_reinversion_pct":50,"reparto_margara_pct":30,"reparto_valqui_pct":30}`
- WHEN validated (sum 110)
- THEN 422 with error on distribution fields

#### Scenario: Concurrent patch serialized

- GIVEN two concurrent `PATCH` requests
- WHEN both execute with `FOR UPDATE` lock
- THEN one commits 200 and the other re-validates sum after lock, no lost update

### Requirement: MPC-3: Frontend Adapter for Parametros

The system MUST expose `useMaestros.getParametros/updateParametros` via `isMock ? atelier : api`. `MaestrosView.vue` `costeo` tab `sumaDistribucion` guard MUST remain and backend MUST re-validate sum independently.

#### Scenario: Adapter mock toggle

- GIVEN `VITE_USE_MOCK=false`
- WHEN `useMaestros().updateParametros({distribucion_reinversion_pct:40})` is called
- THEN `PATCH /api/v1/maestros/parametros-costeo` 200

#### Scenario: Frontend guard plus backend guard

- GIVEN `VITE_USE_MOCK=false` and UI sum !=100 shows alert
- WHEN user forces `PATCH` with sum 90 via API directly
- THEN backend returns 422 regardless of frontend state
