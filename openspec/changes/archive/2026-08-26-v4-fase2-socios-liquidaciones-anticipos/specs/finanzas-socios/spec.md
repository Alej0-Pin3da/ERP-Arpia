# Delta for finanzas-socios

## ADDED Requirements

### Requirement: SOC-1 — Socia Extended Profile (10 nullable columns)

The system MUST extend `Socios_Configuracion` with 10 nullable columns matching `SociaAtelier` (ERP-V4 §6.3, atelier.ts:173): `rol VARCHAR(50)`, `banco VARCHAR(100)`, `es_fondo_taller BOOLEAN DEFAULT FALSE`, `telefono VARCHAR(50)`, `email VARCHAR(255)`, `tipo_cuenta VARCHAR(50)`, `numero_cuenta VARCHAR(50)`, `titular_cuenta VARCHAR(150)`, `activo BOOLEAN DEFAULT TRUE`, `notas TEXT`. All columns MUST be nullable with no backfill required; existing rows MUST remain readable. `porcentaje_participacion` and `nombre` MUST remain unchanged.

#### Scenario: Extend existing socia with full profile persists and round-trips

- GIVEN a socia exists with only `nombre` and `porcentaje_participacion`
- WHEN the client PATCHes the socia with all 10 new fields populated
- THEN the response MUST return all 10 fields with the written values and GET by id MUST return them identically

#### Scenario: Existing rows survive migration with nulls

- GIVEN the database has 2 socias created before the migration
- WHEN the migration 0011 has been applied and GET /finanzas/socios is called
- THEN both socias MUST be returned with the 10 new fields as `null` (or defaults for booleans) and no 500 error

#### Scenario: Create socia with minimal fields omitting new columns

- GIVEN no socia named "Nueva"
- WHEN POST /finanzas/socios is called with only `nombre` and `porcentaje_participacion`
- THEN the system MUST create the row with the 10 new fields as `null`/`false`/`true` defaults and return 201

### Requirement: SOC-2 — Socia Field Validation and Sum-to-100 Invariant (including fondo)

The system MUST validate field constraints and MUST enforce the sum-to-100 invariant over `porcentaje_participacion` across all rows where `activo = true`, including the row with `es_fondo_taller = true` (the 40% fondo IS a socia). Validation: `rol` max 50 chars; `email` MUST match RFC 5321 basic check when present; `tipo_cuenta` SHOULD be one of `AHORROS|CORRIENTE|OTRA` when present; `numero_cuenta` max 50; `es_fondo_taller` at most one active row MAY have `true` (SHOULD reject second). Sum-to-100 MUST be checked on create/update/toggle-activo and MUST return 422 on violation. Service-layer check (Postgres cannot enforce cross-row sum via CHECK — see finanzas.py pattern).

#### Scenario: Sum exceeds 100 including fondo is rejected

- GIVEN active socias Fondo 40 + Margarita 30 + Valqui 30 sum to 100
- WHEN a client tries to PATCH Margarita to 35
- THEN the system MUST return 422 with an error indicating the sum would be 105

#### Scenario: Invalid email is rejected

- GIVEN a valid socia payload
- WHEN `email` is "not-an-email"
- THEN the system MUST return 422 and MUST NOT create or modify the row

#### Scenario: Second fondo is rejected

- GIVEN one active socia already has `es_fondo_taller = true`
- WHEN a second socia is created or patched with `es_fondo_taller = true`
- THEN the system SHOULD return 422 indicating only one active fondo is allowed

### Requirement: SOC-3 — Socia Filtering and Query

The system MUST support filtering `GET /finanzas/socios` by `activo` (bool), `es_fondo_taller` (bool), `rol` (exact), and `q` (case-insensitive substring on `nombre`, `email`, `telefono`). Filters MUST be composable. Results MUST be paginated with existing pagination conventions. Filtering MUST NOT affect the sum-to-100 invariant.

#### Scenario: Filter active socias excludes inactive

- GIVEN 3 socias where one has `activo = false`
- WHEN GET /finanzas/socios?activo=true is called
- THEN the response MUST contain exactly 2 socias and MUST NOT include the inactive one

#### Scenario: Search by q returns matching socias

- GIVEN socias "Margarita" and "Valqui"
- WHEN GET /finanzas/socios?q=marg is called
- THEN the response MUST contain Margarita and MUST NOT contain Valqui

#### Scenario: Filter by es_fondo_taller returns only the fondo

- GIVEN one socia is the 40% fondo and two are persons
- WHEN GET /finanzas/socios?es_fondo_taller=true is called
- THEN the response MUST contain exactly 1 row with `es_fondo_taller = true`
