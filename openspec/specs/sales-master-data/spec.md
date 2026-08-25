# sales-master-data Specification

## Purpose

Minimal master seeds for channels and payment methods to enable validation and zero-manual-setup deploys, with idempotent migrations and VARCHAR->FK follow-up path.

## Requirements

### Requirement: SMD-1: Master Channels Seed

The system MUST seed `maestros_canales_venta` with 5 canonical rows: `web`, `whatsapp`, `instagram`, `feria`, `showroom_pereira` (columns `clave`/`nombre` or `codigo` per model). Seed MUST be idempotent (re-run produces no duplicates). `ventas.canal_venta` validation SHOULD reference this table when FK migration completes; in this phase, VARCHAR enum is source of truth.

#### Scenario: Initial migration seeds 5 channels

- GIVEN an empty `maestros_canales_venta` table
- WHEN migration `0010_fix_ventas_canal_y_metodo_pago` runs
- THEN 5 rows exist with expected claves

#### Scenario: Seed idempotency

- GIVEN the 5 rows already exist
- WHEN migration/seeder is re-run
- THEN row count remains 5

### Requirement: SMD-2: Master Payment Methods Seed

The system MUST seed `maestros_metodos_pago` with canonical values: `efectivo`, `transferencia`, `tarjeta`, `contraentrega` (at minimum 3). Seed MUST be idempotent. `Ventas.metodo_pago` validation SHOULD accept only seeded values plus NULL; unknown values SHOULD return 422 after seed is present.

#### Scenario: Seeds payment methods

- GIVEN an empty `maestros_metodos_pago` table
- WHEN seeder runs
- THEN at least 3 rows exist

#### Scenario: Invalid metodo_pago rejected against masters

- GIVEN seeds present
- WHEN `POST /api/v1/ventas` with `metodo_pago: "cripto"`
- THEN status is 422

### Requirement: SMD-3: Frontend Mode and Adapter Reuse

The frontend MUST provide `src/services/api/clientes.ts` and `src/composables/useClientes.ts` adapter that switches via `VITE_USE_MOCK` and `GET /api/__mode`. The existing `__mode` badge MUST display real/mock. `src/stores/atelier.ts` MUST be annotated `@deprecated` (not deleted).

#### Scenario: Mode badge reflects backend

- GIVEN `VITE_USE_MOCK=false`
- WHEN app boots
- THEN `GET /api/__mode` returns `{mode:"real"}` and badge shows "Real"

#### Scenario: Deprecated store preserved

- GIVEN the change is applied
- WHEN inspecting `src/stores/atelier.ts`
- THEN file contains `@deprecated — use composables + api services (V4 Fase 1)` and still exports for mock path
