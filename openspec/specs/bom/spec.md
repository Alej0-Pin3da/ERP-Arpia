# bom Specification

## Purpose

Recipe management nested under each product: raw-material lines (`BOM_Insumos`) with optional variant binding and waste, and combo lines (`BOM_Productos`). `cantidad_requerida` uses the insumo's master `unidad_medida`. API prefix `/api/v1`. Money and quantities `NUMERIC(15,4)`.

## Requirements

### Requirement: BOM_Insumos nested CRUD

The system MUST expose `POST/GET /productos/{id}/bom/insumos` and `PUT/DELETE /productos/{id}/bom/insumos/{bom_id}` (POST 201, DELETE 204). A missing product MUST return 404. `insumo_id` MUST reference an existing `Insumo` (400). `variante_id` MUST be nullable and, when present, reference a `Variante_Producto` of the same product (400). `cantidad_requerida` MUST be > 0 and `porcentaje_desperdicio` MUST be 0–100 (422).

#### Scenario: Create an insumo line

- GIVEN an admin, an existing product and insumo
- WHEN posting `insumo_id` 5, `cantidad_requerida` 2.5
- THEN 201 returns the line; `porcentaje_desperdicio` defaults 0

#### Scenario: Nonexistent insumo

- GIVEN no insumo with `id` 999
- WHEN posting `insumo_id` 999
- THEN 400 is returned and nothing is written

#### Scenario: Waste out of range

- WHEN posting `porcentaje_desperdicio` 150
- THEN 422 is returned and nothing is written

#### Scenario: Variant of another product

- GIVEN variant 5 belongs to product 1
- WHEN posting `variante_id` 5 under product 2
- THEN 400 is returned and nothing is written

#### Scenario: Nonexistent parent product

- GIVEN no product with `id` 999
- WHEN reading `/productos/999/bom/insumos`
- THEN 404 is returned

### Requirement: Duplicate insumo-line rule

The system MUST reject with 409 a second row with the same `(producto_id, insumo_id)` and `variante_id IS NULL` (PostgreSQL `NULL != NULL` defeats the unique constraint), and a duplicate non-NULL `(producto_id, insumo_id, variante_id)` row.

#### Scenario: Duplicate NULL-variant row

- GIVEN a line (product 1, insumo 5, variante NULL)
- WHEN posting (insumo 5, variante NULL) again
- THEN 409 is returned and nothing is written

#### Scenario: Duplicate variant-specific row

- GIVEN a line (product 1, insumo 5, variante 3)
- WHEN posting (insumo 5, variante 3) again
- THEN 409 is returned and nothing is written

#### Scenario: NULL rule and variant rule coexist

- GIVEN a line (product 1, insumo 5, variante NULL)
- WHEN posting (insumo 5, variante 3)
- THEN 201 is returned

### Requirement: Variante semantics

A row with `variante_id NULL` MUST be the base rule for ALL variants of the product. A row with `variante_id = X` MUST override (not add to) the base rule for variant X only.

#### Scenario: Base rule applies to all variants

- GIVEN only a NULL-variant line (product 1, insumo 5)
- WHEN the cost engine computes any variant of product 1
- THEN the NULL-variant line is used

#### Scenario: Variant-specific override

- GIVEN a NULL-variant line (insumo 5, qty 1.0) and a variant-3 line (insumo 5, qty 2.0)
- WHEN the cost engine computes variant 3
- THEN qty 2.0 is used and qty 1.0 is not summed

### Requirement: Waste semantics

`porcentaje_desperdicio` MUST apply only to `BOM_Insumos`; effective quantity MUST be `cantidad_requerida × (1 + porcentaje_desperdicio/100)`. `BOM_Productos` MUST NOT carry waste.

#### Scenario: Effective quantity with waste

- GIVEN `cantidad_requerida` 10 and `porcentaje_desperdicio` 20
- WHEN the cost engine uses the line
- THEN effective quantity is 12.0000

### Requirement: BOM_Productos nested CRUD

The system MUST expose `POST/GET /productos/{id}/bom/productos` and `PUT/DELETE /productos/{id}/bom/productos/{bom_id}` (POST 201, DELETE 204). A missing product MUST return 404. `producto_incluido_id` MUST reference an existing `Producto` (400). `cantidad` MUST be > 0 (422). Duplicate `(combo_id, producto_incluido_id)` MUST return 409.

#### Scenario: Create a combo line

- GIVEN an admin and two existing products
- WHEN posting `producto_incluido_id` 2, `cantidad` 3
- THEN 201 returns the combo line

#### Scenario: Duplicate combo line

- GIVEN a combo line (combo 1, product 2)
- WHEN posting `producto_incluido_id` 2 again
- THEN 409 is returned and nothing is written

#### Scenario: Nonexistent included product

- GIVEN no product with `id` 999
- WHEN posting `producto_incluido_id` 999
- THEN 400 is returned and nothing is written
