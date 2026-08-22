# compras-insumos Specification

## Purpose

Registering and querying insumo purchase records (`Compras_Insumos`). Purchases are the first write path over inventory and feed the WAC cost engine. API prefix `/api/v1`. Money and quantities `NUMERIC(15,4)`.

## Requirements

### Requirement: REQ-CI-001 — Register purchase with modo/factura

System MUST expose `POST /api/v1/compras-insumos` with `insumo_id` (RESTRICT), optional `proveedor_id` (SET NULL, 400 if missing), `cantidad_comprada>0`, `modo TOTAL|UNIT` (default UNIT), `precio_unitario` (UNIT) or `costo_total` (TOTAL), optional `factura` ≤100. TOTAL MUST derive `price=costo_total/qty` in Decimal. `qty<=0|cost<=0|Infinity|NaN` MUST 422 before write. `fecha_compra` server-set. 201 + `CompraInsumoRead` + atomic WAC. (Prev: no modo/factura/Infinity guard.)

#### Scenario: SCN-CI-001 — TOTAL purchase
- GIVEN stock 10@5, POST qty10 costo_total90 modoTOTAL facturaF-001
- WHEN succeeds
- THEN 201, unit9, stock20, cost7.0000, factura stored

#### Scenario: SCN-CI-002 — Rejects invalid
- GIVEN qty<=0 or cost<=0 or Infinity
- WHEN POST
- THEN 422 no write no stock change

#### Scenario: SCN-CI-003 — Unknown FK
- GIVEN unknown insumo or proveedor
- WHEN POST
- THEN 404 for insumo, 400 for proveedor

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

The system MUST expose `GET /api/v1/compras-insumos` returning a JSON array of `CompraInsumoRead` ordered by `fecha_compra DESC` (and `id DESC` as tie-breaker), honoring `limit` and `offset`, and SHALL optionally filter by `insumo_id`.

#### Scenario: Paginated list

- Given existing purchases, when GET with `limit=2&offset=2`, the system returns at most 2 rows and skips the first 2 in `fecha_compra DESC` order.

#### Scenario: Filter by insumo

- Given purchases across two insumos, when GET with `insumo_id=<id>`, the system returns only purchases for that insumo.

### Requirement: REQ-CI-002 — Response shape

`CompraInsumoCreate` MUST accept `insumo_id`, optional `proveedor_id`, `cantidad_comprada`, `precio|costo_total`, `modo`, `factura`. `CompraInsumoRead` MUST include `id`, `insumo_id`, nullable `proveedor_id`, server-set `fecha_compra`, `cantidad_comprada`, `precio_unitario_compra`, `factura`, `costo_unitario_aplicado` as `NUMERIC(15,4)` strings. (Prev: no modo/factura.)

#### Scenario: SCN-CI-004 — Shape
- GIVEN persisted purchase
- WHEN read
- THEN all fields present, decimals 4-place strings

### Requirement: REQ-CI-003 — History and CSV

System MUST expose `GET /api/v1/compras-insumos?insumo_id=X` ordered `fecha_compra DESC`; any authenticated MAY read. `HistorialDrawer.vue` MUST show date, qty, prev→new stock/cost, total, factura. CSV MUST export same columns with header `fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura`.

#### Scenario: SCN-CI-005 — Drawer + CSV + RBAC
- GIVEN 2 purchases for insumo
- WHEN opening drawer then Export CSV
- THEN rows show prev→new stock/cost factura; CSV header `fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura`; consulta GET 200 POST 403

### Requirement: REQ-CI-004 — Inventory view actions

`InventarioView.vue` MUST add per-row `+ Compra` (opens ComprasForm with insumo_id) and `History` (opens HistorialDrawer); consulta sees History only. `canPurchase` (admin|operador) gates `+ Compra`.

#### Scenario: SCN-CI-006 — Wiring
- GIVEN operador vs consulta on InventarioView
- WHEN row rendered then click +Compra
- THEN operador form pre-filled; consulta +Compra hidden History visible

## Decision: no `fecha_compra` range filter this phase

- The proposal open question asks whether GET filters by a purchase-date range. Decided: NOT offered in this phase; only `insumo_id` filtering SHALL be scoped separately (Phase 5+ reporting may add date ranges).
