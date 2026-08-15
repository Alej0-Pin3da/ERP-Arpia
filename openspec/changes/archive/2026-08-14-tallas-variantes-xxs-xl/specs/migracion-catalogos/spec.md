# migracion-catalogos Specification

## Purpose

Migration-pipeline capabilities for size variants. F1 seeds variants from `variantes` tuples in `PRODUCTOS_CATALOGO` (reusing `upsert_producto`; no schema change), adds the missing Set Celeno product at the locked price, F5 omits + reports size-less rows and stays idempotent across the NULL→variant transition, and F7 validation is aware of both. No API surface; behavior is exercised through the migrate CLI (F0–F7) and `backend/tests/test_migrate_*.py`.

## Requirements

### Requirement: MIG-1: Variant seeding via PRODUCTOS_CATALOGO tuples

F1 (catalog) SHALL seed variants from `variantes` tuples in `PRODUCTOS_CATALOGO` (`backend/migrate/catalog.py`) through `upsert_producto`, which SHALL deduplicate by `(producto_id, nombre_variante)` and create `Variante_Producto` rows with `precio_venta` NULL (sizes share the product price). A product without a `variantes` tuple MUST NOT receive a phantom NULL-variant row.

#### Scenario: Seeds 30 variants across the five sized products

- GIVEN the catalog plan with `variantes` = (XXS, XS, S, M, L, XL)
- WHEN F1 applies `upsert_producto` for Set Aelo, Set Ocipete, Set Celeno, Blusa Manga Larga, Blusa Manga Corta
- THEN each product has exactly 6 variants (30 total) with `precio_venta` NULL

#### Scenario: Re-run does not duplicate variants

- GIVEN the 30 variants already persisted
- WHEN F1 is run again
- THEN no `Variante_Producto` row is created a second time (manual dedup guard)

#### Scenario: Non-sized products get no variant rows

- GIVEN products without a `variantes` tuple (e.g. Corset Garras, combos)
- WHEN F1 runs
- THEN those products have zero `Variante_Producto` rows

### Requirement: MIG-2: Set Celeno catalog entry

`PRODUCTOS_CATALOGO` SHALL include the product "Set Celeno" (tipo "Set") with `precio_venta_sugerido` 75000. The catalog product count SHALL be 14. No BOM recipe or combo wiring is added in this change.

#### Scenario: Set Celeno is created at the locked price

- GIVEN a `PRODUCTOS_CATALOGO` entry for "Set Celeno" at 75000
- WHEN F1 runs
- THEN "Set Celeno" exists with `precio_venta_sugerido` 75000 and `conteo_productos == 14`

#### Scenario: Workbook 65000 is not used

- GIVEN the workbook shows Set Celeno at 65000 in one CAJAS block
- WHEN F1 runs
- THEN the persisted price is 75000 (locked decision), documented in the report

### Requirement: MIG-3: F5 omits and reports size-less rows

F5 (ventas) SHALL omit any plan line whose product HAS variants but the row resolves no variant, and SHALL report (product, date, quantity, reason). The omit MUST happen before the material explosion so the `inventory.py` root guard (`explosion_materiales`, variante required when `producto.variantes` is non-empty) never raises `DomainValidationError`. F5 MUST NOT invent a default variant.

#### Scenario: The two size-less rows are omitted and the phase completes

- GIVEN plan rows SET OCIPETE 28/3 and BLUSA ARPIA MANGA LARGA 5/8 with no size
- WHEN F5 runs
- THEN those rows are omitted with a report entry (product, date, qty, reason) and the remaining 19 rows are inserted

#### Scenario: No default variant is invented

- GIVEN a size-less row for a sized product
- WHEN F5 runs
- THEN no `DetalleVenta` is written with an invented `variante_id` (VTA-4/EXM-2)

### Requirement: MIG-4: F5 NULL-matching idempotency

`_contar_existentes` (`backend/migrate/sales.py`) SHALL count an existing `DetalleVenta` row with `variante_id` NULL as a match when the plan line resolves a variant. This keeps the NULL→variant transition self-contained; delete+reinsert of existing rows is rejected.

#### Scenario: Re-run after seeding does not duplicate the 21 sales

- GIVEN 21 persisted detail rows with `variante_id` NULL and variants seeded
- WHEN F5 is re-run
- THEN `_contar_existentes` matches the NULL rows and no new rows are inserted

#### Scenario: NULL plan line still matches NULL DB row

- GIVEN a combo line that resolves no variant
- WHEN `_contar_existentes` runs
- THEN it matches only rows with `variante_id IS NULL`

### Requirement: MIG-5: N7 validation aware of omissions and NULL-matching

F7 validation SHALL mirror F5 semantics: `_n7g_idempotencia` MUST NOT flag the two omitted rows, and MUST resolve DB rows with `variante_id` NULL as matching plan lines that resolve a variant, so a re-run validates clean. `_n7a_conteos` SHALL report the 14-product catalog as present.

#### Scenario: Validation passes after the migrated state

- GIVEN the post-migration DB (14 products, 30 variants, 19 sales, 2 omitted)
- WHEN F7 runs
- THEN N7a reports productos 14/14 and N7g reports no duplicate natural keys