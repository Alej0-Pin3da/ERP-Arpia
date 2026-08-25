# ventas-channel-payment Specification

## Purpose

Align `Ventas` sales channel and payment method: add nullable `metodo_pago`, normalize `canal_venta` to canonical enum, validate against masters, and expose adapter services.

## Requirements

### Requirement: VCP-1: Ventas Payment Method

The system MUST add `metodo_pago` VARCHAR(50) nullable to `Ventas`. `VentaCreate`/`VentaRead` MUST include it. Values SHOULD be validated against `maestros_metodos_pago` canonical set when that table is seeded; NULL MUST be accepted. Migration MUST be reversible.

#### Scenario: Create venta with valid metodo_pago

- GIVEN `POST /api/v1/ventas` with `metodo_pago: "transferencia"`
- WHEN processed
- THEN status is 201 and `metodo_pago` persists and returns on GET

#### Scenario: Null metodo_pago allowed

- GIVEN `POST /api/v1/ventas` without `metodo_pago`
- WHEN processed
- THEN status is 201 and `metodo_pago` is null

### Requirement: VCP-2: Canal Venta Canonical Alignment

The system MUST align `canal_venta` to enum `web | whatsapp | instagram | feria | showroom_pereira`. `VentaCreate` MUST reject any other value with 422. Existing constraint MUST be migrated to this set. The column MUST remain VARCHAR(50) in this phase (FK follow-up later).

#### Scenario: Valid canal accepted

- GIVEN `POST /api/v1/ventas` with `canal_venta: "whatsapp"`
- WHEN processed
- THEN status is 201

#### Scenario: Invalid canal rejected

- GIVEN `POST /api/v1/ventas` with `canal_venta: "telefono"`
- WHEN validated
- THEN status is 422 with field error on `canal_venta`

### Requirement: VCP-3: Ventas Frontend Adapter

The frontend MUST provide `src/services/api/ventas.ts` and consume it via composable (or `useClientes` adapter pattern) with a `VITE_USE_MOCK` switch. When `VITE_USE_MOCK=false`, sales MUST hit `/api/v1/ventas`; when true, MUST use `src/stores/atelier.ts` mock. `*.vue` files MUST remain structurally intact (no rewrite).

#### Scenario: Mock toggle routes to API

- GIVEN `VITE_USE_MOCK=false` and backend reachable
- WHEN `useVentas().create({canal_venta: "web"})` is called
- THEN network shows `POST /api/v1/ventas` 201 and `GET /api/__mode` confirms real mode

#### Scenario: Vue components unchanged

- GIVEN the adapter is active
- WHEN diffing `*.vue` files vs base
- THEN no structural changes (only import of composable if needed)
