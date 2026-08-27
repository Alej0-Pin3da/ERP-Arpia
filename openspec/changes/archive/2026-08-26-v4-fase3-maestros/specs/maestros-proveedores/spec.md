# Delta for maestros-proveedores

## ADDED Requirements

### Requirement: MP-1: Proveedor Catalog CRUD

The system MUST provide Paginated CRUD for `maestros_proveedores` at `GET /api/v1/maestros/proveedores` (`limit/offset/q/categoria/ciudad/activo/sort_by/order`), `POST 201`, `PATCH /{id}`, `DELETE /{id}`. `nombre` MUST be UNIQUE. Fields: `categoria` free VARCHAR(100), `ciudad` VARCHAR(80), `calificacion` NUMERIC(3,1) `ge=0 le=5`, `tiempo_entrega_dias` INT `ge=0`, `email` EmailStr, `activo` bool default true. Duplicate `nombre` MUST return 409; invalid enum/email MUST return 422.

#### Scenario: Create proveedor persists

- GIVEN `POST /api/v1/maestros/proveedores` with `{"nombre":"Telas Atenea","categoria":"Telas Principales","ciudad":"Pereira","calificacion":4.8}`
- WHEN processed
- THEN status is 201 and `GET /maestros/proveedores/{id}` returns matching fields and `GET` list includes it

#### Scenario: Duplicate nombre rejected

- GIVEN a proveedor named "Telas Atenea" exists
- WHEN `POST /api/v1/maestros/proveedores` with same `nombre` (case-insensitive trim) is called
- THEN status is 409 with error on `nombre`

#### Scenario: List with filters paginated

- GIVEN 6 seed proveedores across 2 categorias
- WHEN `GET /api/v1/maestros/proveedores?q=atenea&categoria=Telas Principales&limit=2&offset=0` is called
- THEN response is `Paginated` with `total` filtered count and `items` length <=2

### Requirement: MP-2: Proveedor Validation and Frontend Adapter

The system MUST expose `src/services/api/maestros.ts` proveedor client and `src/composables/useMaestros.ts` adapter. `useMaestros` MUST route via `isMock ? atelier : api` using `useMode`. `MaestrosView.vue` proveedores tab MUST remain structurally intact and call `useMaestros` for `guardar/eliminar`. State MUST survive `F5`.

#### Scenario: Adapter routes by mode

- GIVEN `VITE_USE_MOCK=false` and backend reachable
- WHEN `useMaestros().listProveedores({q:"atenea"})` is called
- THEN network shows `GET /api/v1/maestros/proveedores?q=atenea` 200 and `GET /api/__mode` is `real`

#### Scenario: Validation boundary

- GIVEN `POST /maestros/proveedores` with `calificacion: 6` or `email: "not-an-email"` or `tiempo_entrega_dias: -1`
- WHEN validated
- THEN status is 422

### Requirement: MP-3: Proveedor Deletion and Audit

The system SHOULD allow `DELETE /maestros/proveedores/{id}` for catalogs with no FK dependents (decoupled from `Compras_Insumos` per 0008). Deletion MUST be hard delete and idempotent 404 on missing.

#### Scenario: Delete proveedor

- GIVEN an existing proveedor
- WHEN `DELETE /maestros/proveedores/{id}` is called then `GET /{id}` again
- THEN first is 204 and second is 404
