# Delta for ventas-channel-payment

## MODIFIED Requirements

### Requirement: VCP-1: Ventas Payment Method

The system MUST add `metodo_pago` VARCHAR(50) nullable to `Ventas` and extend `maestros_metodos_pago` from 0010 stub (`codigo,nombre`) to full catalog (`nombre UNIQUE, tipo Literal TRANSFERENCIA|BILLETERA_DIGITAL|EFECTIVO|PASARELA_DATAFONO, comision_pct NUMERIC(15,4) ge=0 le=100, tiempo_acreditacion VARCHAR(50), activo bool default true, datos_cuenta TEXT nullable`). `VentaCreate`/`VentaRead` MUST include `metodo_pago`. `GET /api/v1/maestros/metodos-pago` MUST be Paginated with `q/tipo/activo/sort_by/order`; `POST 201/PATCH/DELETE` MUST follow catalog pattern with `tryFetch` fallback in frontend. NULL `metodo_pago` MUST be accepted.
(Previously: stub-only `metodo_pago` column with no catalog CRUD)

#### Scenario: Create venta with valid metodo_pago

- GIVEN `POST /api/v1/ventas` with `metodo_pago: "transferencia"`
- WHEN processed
- THEN status is 201 and `metodo_pago` persists and returns on GET

#### Scenario: Null metodo_pago allowed

- GIVEN `POST /api/v1/ventas` without `metodo_pago`
- WHEN processed
- THEN status is 201 and `metodo_pago` is null

#### Scenario: MetodoPago catalog CRUD

- GIVEN `POST /api/v1/maestros/metodos-pago` with `{"nombre":"Nequi","tipo":"BILLETERA_DIGITAL","comision_pct":1.5}`
- WHEN fetched via `GET /maestros/metodos-pago?tipo=BILLETERA_DIGITAL`
- THEN it appears filtered and duplicate `nombre` returns 409

### Requirement: VCP-2: Canal Venta Canonical Alignment

The system MUST align `canal_venta` to enum `web | whatsapp | instagram | feria | showroom_pereira` and extend `maestros_canales_venta` from 0010 stub to full catalog (`nombre UNIQUE, tipo Literal FISICO|DIGITAL|EVENTO, comision_pct NUMERIC(15,4) ge=0 le=100, costo_fijo_mensual NUMERIC(15,4) ge=0, activo bool default true, descripcion TEXT nullable`). `VentaCreate` MUST reject any other value with 422. `GET /api/v1/maestros/canales-venta` MUST be Paginated with `q/tipo/activo/sort_by/order`; `POST 201/PATCH/DELETE` follow catalog pattern. Migration MUST use `_has_column` guards and nullable ALTER to avoid 0010 collision. Column MUST remain VARCHAR(50) in this phase.
(Previously: stub-only canales table with no tipo/comision/costo columns)

#### Scenario: Valid canal accepted

- GIVEN `POST /api/v1/ventas` with `canal_venta: "whatsapp"`
- WHEN processed
- THEN status is 201

#### Scenario: Invalid canal rejected

- GIVEN `POST /api/v1/ventas` with `canal_venta: "telefono"`
- WHEN validated
- THEN status is 422 with field error on `canal_venta`

#### Scenario: Canal catalog extend is reversible

- GIVEN `alembic upgrade head` applied
- WHEN `alembic downgrade -1` is run
- THEN added columns are dropped but stub table `maestros_canales_venta` remains

### Requirement: VCP-3: Ventas Frontend Adapter

The frontend MUST provide `src/services/api/ventas.ts` and consume it via composable with `VITE_USE_MOCK` switch. Additionally `src/services/api/maestros.ts` MUST expose `canales-venta`/`metodos-pago` clients via `tryFetch('/maestros/...', fallbackStaticArrays)` preserving 0010 fallback. When `VITE_USE_MOCK=false`, maestros catalog calls MUST hit API; when true, MUST use `atelier.ts` mock. `*.vue` files MUST remain structurally intact.
(Previously: only stub tryFetch for canales/metodos without full CRUD)

#### Scenario: Mock toggle routes to API

- GIVEN `VITE_USE_MOCK=false` and backend reachable
- WHEN `useVentas().create({canal_venta: "web"})` is called
- THEN network shows `POST /api/v1/ventas` 201 and `GET /api/__mode` confirms real mode

#### Scenario: Vue components unchanged

- GIVEN the adapter is active
- WHEN diffing `*.vue` files vs base
- THEN no structural changes (only import of composable if needed)

#### Scenario: tryFetch fallback preserved

- GIVEN backend unreachable and `VITE_USE_MOCK=true`
- WHEN `listCanales()` is called
- THEN fallback static 5 `codigo/nombre` array is returned without error
