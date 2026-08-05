# compras-insumos Specification

## Purpose

Registering and querying insumo purchase records (`Compras_Insumos`). Purchases are the first write path over inventory and feed the WAC cost engine. API prefix `/api/v1`. Money and quantities `NUMERIC(15,4)`.

## Requirements

### Requirement: Register an insumo purchase

The system MUST expose `POST /api/v1/compras-insumos` accepting a `CompraInsumoCreate` payload to persist a `CompraInsumo` row. `insumo_id` MUST be required (FK `RESTRICT`). `proveedor_id` MUST be optional (FK `SET NULL`) and, when present, MUST reference an existing `Proveedor` (400 otherwise). `cantidad_comprada` MUST be > 0 and `precio_unitario_compra` MUST be >= 0; invalid values MUST be rejected with 422 before any DB write. `fecha_compra` MUST be set by the server (`func.now()`). Success MUST return 201 with a `CompraInsumoRead`.

#### Scenario: Create a purchase with optional proveedor

- GIVEN an authenticated admin or operador, an existing `Insumo`, and an existing `Proveedor`
- WHEN a valid `CompraInsumoCreate` is posted with a positive quantity and unit price
- THEN a `CompraInsumo` is persisted and a 201 responds with `CompraInsumoRead`

#### Scenario: Purchase without proveedor

- WHEN a valid payload omits `proveedor_id`, the purchase is created with `proveedor_id` null.

#### Scenario: Nonexistent insumo

- When `insumo_id` has no matching `Insumo`, the system MUST return 404 and write nothing.

#### Scenario: Invalid proveedor

- When `proveedor_id` has no matching `Proveedor`, the system MUST return 400.

#### Scenario: Non-positive quantity or negative price

- When `cantidad_comprada <= 0` or `precio_unitario_compra < 0`, the system MUST return 422 with no DB write.

### Requirement: Authorization for purchase operations

`GET /api/v1/compras-insumos` MUST allow any authenticated role (`admin`, `operador`, `consulta`). `POST /api/v1/compras-insumos` (and any other mutation) MUST allow only `admin` or `operador`; a `consulta` user MUST receive 403 and an unauthenticated request MUST receive 401.

#### Scenario: Unauthenticated POST

- Given no bearer token, when posting a purchase, a 401 is returned.

#### Scenario: Consulta POST forbidden

- Given a `consulta` token, when POST with a valid payload, the system returns 403.

#### Scenario: Operador POST allowed

- Given an `operador` token, when POST a valid purchase, the system returns 201.

#### Scenario: Any role reads

- Given a `consulta` token, when GET purchases, the system returns 200.

### Requirement: List purchases with pagination and filter

The system MUST expose `GET /api/v1/compras-insumos` returning a JSON array of `CompraInsumoRead` ordered by `id`, honoring `limit` and `offset`, and SHALL optionally filter by `insumo_id`.

#### Scenario: Paginated list

- Given existing purchases, when GET with `limit=2&offset=2`, the system returns at most 2 rows and skips the first 2.

#### Scenario: Filter by insumo

- Given purchases across two insumos, when GET with `insumo_id=<id>`, the system returns only purchases for that insumo.

### Requirement: Response shape

`CompraInsumoCreate` MUST accept `insumo_id`, optional `proveedor_id`, `cantidad_comprada`, `precio_unitario_compra`. `CompraInsumoRead` MUST include `id`, `insumo_id`, nullable `proveedor_id`, server-set `fecha_compra`, `cantidad_comprada`, `precio_unitario_compra`.

#### Scenario: Read shape completeness

- Given persisted purchase, the returned `CompraInsumoRead` contains the full field set bounded above with Numeric decimals as strings.

## Decision: no `fecha_compra` range filter this phase

- The proposal open question asks whether GET filters by a purchase-date range. Decided: NOT offered in this phase; only `insumo_id` filtering SHALL be scoped separately (Phase 5+ reporting may add date ranges).