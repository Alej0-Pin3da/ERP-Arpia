# Delta for maestros-categorias-ubicaciones

## ADDED Requirements

### Requirement: MCU-1: CategoriaColeccion Catalog

The system MUST provide Paginated CRUD for `maestros_categoria_coleccion` at `GET /maestros/categorias-coleccion` (`limit/offset/q/tipo_talla/activo/sort_by/order`), `POST 201`, `PATCH /{id}`, `DELETE /{id}`. Fields: `nombre` VARCHAR(100) UNIQUE, `tipo_talla` Literal `CON_TALLAS_ESTANDAR|SIN_TALLA_MERCH|TALLA_UNICA` with CHECK, `descripcion` TEXT nullable, `margen_meta_pct` NUMERIC(15,4) `ge=0 le=100` nullable, `total_modelos` INT `ge=0` default 0, `activo` bool default true. Duplicate `nombre` MUST 409; invalid `tipo_talla` MUST 422.

#### Scenario: Create categoria

- GIVEN `POST /maestros/categorias-coleccion` with `{"nombre":"Atenea Rollos","tipo_talla":"CON_TALLAS_ESTANDAR","margen_meta_pct":35}`
- WHEN processed
- THEN 201 and `GET` list filtered by `tipo_talla=CON_TALLAS_ESTANDAR` includes it

#### Scenario: Duplicate nombre rejected

- GIVEN categoria "Atenea Rollos" exists
- WHEN `POST` with same `nombre` is called
- THEN 409

#### Scenario: Invalid tipo_talla rejected

- GIVEN `POST` with `tipo_talla: "INVALID"`
- WHEN validated
- THEN 422

### Requirement: MCU-2: UbicacionTaller Catalog

The system MUST provide Paginated CRUD for `maestros_ubicacion_taller` at `GET /maestros/ubicaciones-taller` (`limit/offset/q/tipo/activo/sort_by/order`), `POST 201`, `PATCH /{id}`, `DELETE /{id}`. Fields: `codigo` VARCHAR(20) UNIQUE matching `UB-*` pattern, `nombre` VARCHAR(100) UNIQUE, `tipo` Literal `ROLLOS_TELAS|GAVETAS_HERRAJES|PERCHERO_SHOWROOM|ACCESORIOS_BODEGA` with CHECK, `capacidad` VARCHAR(100) free nullable, `observaciones` TEXT nullable, `activo` bool default true. Duplicate `codigo` or `nombre` MUST 409.

#### Scenario: Create ubicacion

- GIVEN `POST /maestros/ubicaciones-taller` with `{"codigo":"UB-A1","nombre":"Estante Atenea A1","tipo":"ROLLOS_TELAS","capacidad":"25 Rollos"}`
- WHEN processed
- THEN 201 and list `GET ?tipo=ROLLOS_TELAS` includes it

#### Scenario: Duplicate codigo rejected

- GIVEN ubicacion `UB-A1` exists
- WHEN `POST` with same `codigo` is called
- THEN 409

#### Scenario: Invalid tipo rejected

- GIVEN `POST` with `tipo: "UNKNOWN"`
- WHEN validated
- THEN 422 with field error on `tipo`

### Requirement: MCU-3: Frontend Adapter for Categorias/Ubicaciones

The system MUST expose `useMaestros` methods for categorias/ubicaciones routing via `isMock ? atelier : api`. Tabs `categorias`/`ubicaciones` in `MaestrosView.vue` MUST remain intact and survive `F5`.

#### Scenario: Adapter mock toggle

- GIVEN `VITE_USE_MOCK=false`
- WHEN `useMaestros().listCategorias({tipo_talla:"TALLA_UNICA"})` is called
- THEN `GET /api/v1/maestros/categorias-coleccion?tipo_talla=TALLA_UNICA` 200

#### Scenario: Persist after refresh

- GIVEN a categoria created via API
- WHEN page is reloaded (`F5`)
- THEN `GET /maestros/categorias-coleccion` still returns it
