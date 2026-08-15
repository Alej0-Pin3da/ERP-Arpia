# ventas-variantes Specification

## Purpose

Ventas UX for sized products. The register/edit form (`frontend/src/components/ventas/VentasForm.vue`) MUST require a variant selection on any line whose selected product has variants, so a sale can never be submitted without the variant the backend explosion requires. Combos and variant-less products keep a single NULL-variant line with no selection. The `productos` API and `Variante_Producto` CRUD are unchanged.

## Requirements

### Requirement: VV-1: Variant required for sized products

For any `detalle` whose selected product has at least one variant, VentasForm SHALL require `variante_id` before submit: the form MUST block submission client-side with a warning and MUST NOT emit the payload until a variant is chosen. The emitted `VentaCreate` MUST carry `variante_id` for that line.

#### Scenario: Sized product without variant is blocked

- GIVEN a sized product with variants (e.g. Set Aelo) selected in a line
- WHEN the user submits without choosing a variant
- THEN the form shows a warning and emits no `submit` event

#### Scenario: Sized product with variant submits

- GIVEN a sized product selected and a variant chosen (e.g. XL)
- WHEN the user submits
- THEN `submit` fires with `variante_id` present in that detail

### Requirement: VV-2: Select hidden or disabled without variants

When no product is selected, or the selected product has zero variants, the variant select SHALL be disabled or hidden and SHALL NOT be required.

#### Scenario: Variant-less product does not require a variant

- GIVEN a product with no variants (e.g. Corset Garras)
- WHEN the user submits the line without a variant
- THEN the payload omits `variante_id` and the sale proceeds

#### Scenario: Empty line select is disabled

- GIVEN a detail row with `producto_id` null
- WHEN the form renders
- THEN the variant select is disabled

### Requirement: VV-3: Combos remain single-line NULL-variant

Combos SHALL NOT require variants; a combo sale SHALL stay one detail row with `variante_id` NULL. Per-component sizes are a documented limitation (`BomProducto.variante_id` out of scope).

#### Scenario: Combo sale needs no variant

- GIVEN a combo product (e.g. Caja Saca Las Garras) selected
- WHEN the user submits without a variant
- THEN the payload contains one detail with no `variante_id`

### Requirement: VV-4: Lazy variant loading drives the requirement

VentasForm SHALL load each product's variants lazily via `productosApi.listVariantes` and cache them per product; the required/hidden decision SHALL be based on the loaded list length.

#### Scenario: Loaded variants populate the select

- GIVEN a sized product selected and its variants loaded
- WHEN the variant select renders
- THEN it lists the 6 sizes and is required

#### Scenario: Empty list disables the requirement

- GIVEN a product whose loaded variant list is empty
- WHEN the select renders
- THEN it is disabled/hidden and not required