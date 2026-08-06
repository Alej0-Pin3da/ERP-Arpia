# productos Specification

## Purpose

Product master data: product types (`Tipos_Producto`), products (`Productos`) and product variants (`Variantes_Producto`) nested under their product. API prefix `/api/v1`. Money `NUMERIC(15,4)`. Mutations require admin; reads require any authenticated role.

## Requirements

### Requirement: Tipo_Producto CRUD

The system MUST expose `POST /tipos-producto` (201), `GET /tipos-producto` (paginated `limit`/`offset`, ordered by `id`), `GET /tipos-producto/{id}`, `PUT /tipos-producto/{id}` and `DELETE /tipos-producto/{id}` (204). `nombre` MUST be required, unique and ≤ 150 chars. A nonexistent type MUST return 404; a duplicate `nombre` MUST return 409.

#### Scenario: Create a type

- GIVEN an admin user and a unique `nombre`
- WHEN `POST /tipos-producto` is called
- THEN a 201 returns the created type with its `id`

#### Scenario: Duplicate type name

- GIVEN an existing type named "Terminado"
- WHEN `POST /tipos-producto` with `nombre` "Terminado"
- THEN the system returns 409 and creates nothing

#### Scenario: Read missing type

- GIVEN no type with `id` 999
- WHEN `GET /tipos-producto/999`
- THEN the system returns 404

#### Scenario: Paginated listing

- GIVEN 5 types
- WHEN `GET /tipos-producto?limit=2&offset=2`
- THEN at most 2 rows are returned, skipping the first 2, ordered by `id`

### Requirement: Producto CRUD

The system MUST expose `POST /productos` (201), `GET /productos` (paginated `limit`/`offset`), `GET /productos/{id}`, `PUT /productos/{id}` and `DELETE /productos/{id}` (204). `tipo_producto_id` MUST reference an existing type (400 otherwise). `requiere_fabricacion` MUST default True; `costos_operativos_fijos` and `precio_venta_sugerido` MUST default 0 and be ≥ 0 (422 otherwise). A nonexistent product MUST return 404.

#### Scenario: Create a product

- GIVEN an admin user and an existing `tipo_producto_id`
- WHEN `POST /productos` with a valid payload
- THEN a 201 returns the product with defaults applied

#### Scenario: Invalid type reference

- GIVEN no type with `id` 999
- WHEN `POST /productos` with `tipo_producto_id` 999
- THEN the system returns 400 and writes nothing

#### Scenario: Negative fixed cost

- WHEN `POST /productos` with `costos_operativos_fijos` -1
- THEN the system returns 422 and writes nothing

#### Scenario: Read missing product

- GIVEN no product with `id` 999
- WHEN `GET /productos/999`
- THEN the system returns 404

### Requirement: Variante_Producto nested CRUD

The system MUST expose `POST /productos/{id}/variantes` (201), `GET /productos/{id}/variantes`, `PUT /productos/{id}/variantes/{variante_id}` and `DELETE /productos/{id}/variantes/{variante_id}` (204). `nombre_variante` MUST be required and unique per product (409 otherwise). `precio_venta` MUST be nullable and ≥ 0 when present. A missing product or variant MUST return 404.

#### Scenario: Create a variant

- GIVEN an admin user and an existing product
- WHEN `POST /productos/1/variantes` with `nombre_variante` "XL"
- THEN a 201 returns the variant bound to product 1

#### Scenario: Duplicate variant name

- GIVEN a product with variant "XL"
- WHEN `POST /productos/1/variantes` with `nombre_variante` "XL"
- THEN the system returns 409

#### Scenario: Variants of missing product

- GIVEN no product with `id` 999
- WHEN `GET /productos/999/variantes`
- THEN the system returns 404

#### Scenario: Delete missing variant

- GIVEN no variant with `id` 999
- WHEN `DELETE /productos/1/variantes/999`
- THEN the system returns 404

### Requirement: Authorization

All mutation endpoints (POST/PUT/DELETE for types, products and variants) MUST require the `admin` role; `operador` and `consulta` MUST receive 403 and unauthenticated requests MUST receive 401. All GET endpoints MUST allow any authenticated role.

#### Scenario: Unauthenticated mutation

- GIVEN no bearer token
- WHEN `POST /productos`
- THEN the system returns 401

#### Scenario: Operador forbidden mutation

- GIVEN an `operador` token
- WHEN `DELETE /productos/1`
- THEN the system returns 403

#### Scenario: Any role reads

- GIVEN a `consulta` token
- WHEN `GET /productos`
- THEN the system returns 200
