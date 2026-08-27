# Delta for maestros-tallas-estandar

## ADDED Requirements

### Requirement: MT-1: TallaEstandar Matrix CRUD

The system MUST provide Paginated CRUD for `maestros_tallas_estandar` at `GET /maestros/tallas-estandar` (`limit/offset/q/activo/sort_by=orden/order`), `POST 201`, `PATCH /{id}`, `DELETE /{id}`. Fields: `talla` VARCHAR(20) UNIQUE free string (e.g. `XXS..XL`), `orden` INT UNIQUE, `busto/cintura/cadera/reduccion_corset` VARCHAR(50) free display strings, `descripcion` TEXT nullable, `activo` bool default true. Seed MUST contain 6 rows XXS(1)..XL(6). Duplicate `talla` or `orden` MUST 409.

#### Scenario: Create talla with orden

- GIVEN `POST /maestros/tallas-estandar` with `{"talla":"XXL","orden":7,"busto":"84 - 88 cm","cintura":"70 - 74 cm","cadera":"94 - 98 cm"}`
- WHEN processed
- THEN 201 and `GET ?sort_by=orden&order=asc` returns XXS..XXL in order

#### Scenario: Duplicate talla rejected

- GIVEN `talla: "M"` with `orden: 4` exists
- WHEN `POST` with same `talla` or same `orden` is called
- THEN 409

#### Scenario: List sorted by orden

- GIVEN 6 seed tallas
- WHEN `GET /maestros/tallas-estandar?sort_by=orden&order=asc`
- THEN first item `talla` is `XXS` and last is `XL`

### Requirement: MT-2: Talla Validation and Frontend Adapter

The system MUST expose `useMaestros` talla methods via `isMock ? atelier : api`. `MaestrosView.vue` `tallas` tab table MUST remain intact and display matrix from API when `VITE_USE_MOCK=false`. Tallas tab merges `TallaEstandar` table + `ProductoSinTalla` cards but each catalog uses independent API calls.

#### Scenario: Adapter routes by mode

- GIVEN `VITE_USE_MOCK=false`
- WHEN `useMaestros().listTallas({sort_by:"orden"})` is called
- THEN `GET /api/v1/maestros/tallas-estandar?sort_by=orden` 200

#### Scenario: Invalid payload rejected

- GIVEN `POST` with missing `talla` or `orden` as string
- WHEN validated
- THEN 422
