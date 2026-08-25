# clientes-crm Specification

## Purpose

Extended CRM for `Clientes`: 10 new nullable fields, JSONB medidas, city/type indices, filtered search, and frontend adapter keeping `*.vue` intact.

## Requirements

### Requirement: CRM-1: Clientes CRM Schema Extension

The system MUST persist `Clientes` with 10 nullable columns: `ciudad` VARCHAR(80), `direccion` VARCHAR(200), `tipo` VARCHAR(30), `talla_habitual` VARCHAR(10), `talla_superior` VARCHAR(10), `talla_inferior` VARCHAR(10), `categoria_preferida` VARCHAR(50), `tipo_producto_frecuente` VARCHAR(50), `notas` TEXT, `medidas` JSONB. It MUST create indices `ix_clientes_tipo` and `ix_clientes_ciudad`. Existing 4 columns MUST remain unchanged. Migration MUST be reversible and nullable.

#### Scenario: Create cliente with full CRM payload

- GIVEN a `POST /api/v1/clientes` with all 10 CRM fields including `medidas: {"busto": 88}`
- WHEN the request is processed
- THEN status is 201 and persisted row matches all fields

#### Scenario: Nullable defaults and reversibility

- GIVEN a cliente created with only required legacy fields
- WHEN fetched via `GET /api/v1/clientes/{id}`
- THEN 10 CRM fields are null and `alembic downgrade -1` removes them without data loss in legacy columns

### Requirement: CRM-2: Clientes Filtering and Search

The system MUST support `GET /api/v1/clientes` with query params `?tipo=&ciudad=&q=` (all optional, combinable). `tipo` and `ciudad` MUST exact-match; `q` MUST case-insensitive ILIKE on `nombre`, `ciudad`, `direccion`. Results MUST be paginated.

#### Scenario: Filter by tipo and ciudad

- GIVEN 3 clientes with varying `tipo`/`ciudad`
- WHEN `GET /api/v1/clientes?tipo=mayorista&ciudad=Pereira` is called
- THEN only matching rows return

#### Scenario: Free-text search finds by nombre alias

- GIVEN a cliente named "Maria Lopez"
- WHEN `GET /api/v1/clientes?q=maria` is called
- THEN that cliente is in results

### Requirement: CRM-3: Medidas JSONB Flexibility

The system MUST accept `medidas` as a free-form JSON object (dict) on `ClienteCreate`/`ClienteUpdate` and return it unchanged on `ClienteRead`. It MUST reject non-object types with 422. Empty or absent `medidas` MUST persist as NULL.

#### Scenario: Valid medidas round-trips

- GIVEN `PATCH /api/v1/clientes/{id}` with `medidas: {"cintura": 70, "notas": "ajuste"}`
- WHEN fetched again
- THEN `medidas` equals the sent object

#### Scenario: Invalid medidas type rejected

- GIVEN `POST /api/v1/clientes` with `medidas: "88-90"`
- WHEN validated
- THEN status is 422
