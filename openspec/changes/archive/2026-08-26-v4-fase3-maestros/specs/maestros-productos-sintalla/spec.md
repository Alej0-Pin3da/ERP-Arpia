# Delta for maestros-productos-sintalla

## ADDED Requirements

### Requirement: MPS-1: ProductoSinTalla Catalog CRUD

The system MUST provide Paginated CRUD for `maestros_producto_sin_talla` at `GET /maestros/productos-sin-talla` (`limit/offset/q/categoria/activo/sort_by/order`), `POST 201`, `PATCH /{id}`, `DELETE /{id}`. Fields: `nombre` VARCHAR(100) UNIQUE, `categoria` VARCHAR(100) free, `dimensiones` VARCHAR(100) nullable, `materiales` VARCHAR(200) nullable, `descripcion` TEXT nullable, `precio_sugerido` NUMERIC(15,4) `ge=0`, `activo` bool default true. Duplicate `nombre` MUST 409; negative `precio_sugerido` MUST 422.

#### Scenario: Create producto

- GIVEN `POST /maestros/productos-sin-talla` with `{"nombre":"Tote Bag Atenea","categoria":"Merch","precio_sugerido":45000.0000}`
- WHEN processed
- THEN 201 and `GET ?categoria=Merch` includes it

#### Scenario: Duplicate nombre rejected

- GIVEN producto "Tote Bag Atenea" exists
- WHEN `POST` with same `nombre` is called
- THEN 409

#### Scenario: Negative price rejected

- GIVEN `POST` with `precio_sugerido: -10`
- WHEN validated
- THEN 422

### Requirement: MPS-2: Frontend Adapter

The system MUST expose `useMaestros` producto methods via `isMock ? atelier : api`. `MaestrosView.vue` `tallas` tab card section for sin-talla MUST remain intact and render from API when `VITE_USE_MOCK=false` and survive `F5`.

#### Scenario: Adapter mock toggle

- GIVEN `VITE_USE_MOCK=false`
- WHEN `useMaestros().listProductosSinTalla({categoria:"Merch"})` is called
- THEN `GET /api/v1/maestros/productos-sin-talla?categoria=Merch` 200

#### Scenario: Persist after refresh

- GIVEN a producto created via API
- WHEN page reloaded
- THEN list still contains it
