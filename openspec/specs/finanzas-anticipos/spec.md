# Delta for finanzas-anticipos

## ADDED Requirements

### Requirement: ANT-1 — Anticipo Table and Validation

System MUST create `anticipos` per ERP-V4 §6.5: `id PK`, `socia_id FK → Socios_Configuracion.id CASCADE NOT NULL`, `monto NUMERIC(12,2) CHECK >0 NOT NULL`, `fecha DATE DEFAULT CURRENT_DATE NOT NULL`, `estado VARCHAR(20) CHECK PENDIENTE_DESCUENTO|DESCONTADO|ANULADO DEFAULT PENDIENTE_DESCUENTO`, `liquidacion_id FK → liquidaciones.id SET NULL NULL`, `concepto VARCHAR(255)`, `metodo_desembolso VARCHAR(50)`, `comprobante VARCHAR(255)`, `observaciones TEXT`, `creado_en TIMESTAMPTZ`. `monto <=0` MUST return 422; nonexistent `socia_id` MUST return 404/422. Index `ix_anticipos_socia_fecha (socia_id, fecha)` MUST exist.

#### Scenario: Valid create succeeds

- GIVEN socia Margarita id 2 activo exists
- WHEN POST /finanzas/anticipos with socia_id 2, monto 50000, fecha 2026-07-10
- THEN MUST return 201 with estado PENDIENTE_DESCUENTO; GET filter MUST include it

#### Scenario: Non-positive monto rejected

- GIVEN valid socia_id
- WHEN POST with monto 0 or -100
- THEN MUST return 422 and MUST NOT create row

#### Scenario: Nonexistent socia rejected

- GIVEN socia_id 9999 does not exist
- WHEN POST with that socia_id
- THEN MUST return 404 or 422

### Requirement: ANT-2 — State Machine and Liquidacion Discount Link

System MUST enforce `PENDIENTE_DESCUENTO → DESCONTADO` and `PENDIENTE_DESCUENTO → ANULADO` as only valid transitions (StrEnum `AnticipoEstado` + map; `DESCONTADO`/`ANULADO` terminal). Only `PENDIENTE_DESCUENTO` MAY be linked to a liquidacion; linking MUST atomically set `liquidacion_id` and transition to `DESCONTADO`. One anticipo MUST link to at most one liquidacion. `ON DELETE SET NULL` MUST null `liquidacion_id` when liquidacion is deleted while preserving the row. `ANULADO` MUST NOT be discountable.

#### Scenario: Discount links and transitions atomically

- GIVEN anticipo PENDIENTE_DESCUENTO for Margarita
- WHEN liquidacion creation includes that anticipo id
- THEN anticipo MUST be DESCONTADO with liquidacion_id = new liquidacion id

#### Scenario: Double-discount rejected

- GIVEN anticipo already DESCONTADO linked to LIQ-2026-01
- WHEN second liquidacion tries to discount same anticipo
- THEN MUST return 409 and link MUST remain to first liquidacion

#### Scenario: Delete liquidacion nulls link, preserves row

- GIVEN DESCONTADO anticipo linked to BORRADOR liquidacion
- WHEN DELETE /finanzas/liquidaciones/{id}
- THEN anticipo MUST survive with liquidacion_id = NULL

### Requirement: ANT-3 — Race Guard for Double-Discount

System MUST prevent concurrent double-discount via partial unique index (e.g. `UNIQUE (id) WHERE estado='DESCONTADO'` or `WHERE liquidacion_id IS NOT NULL`) and `SELECT ... FOR UPDATE` on anticipo rows inside the liquidacion transaction. Concurrent second attempt MUST return 409 (not 500); first link MUST remain intact after failure.

#### Scenario: Concurrent discount yields one 201 and one 409

- GIVEN PENDIENTE_DESCUENTO anticipo and two concurrent POST /finanzas/liquidaciones referencing it
- WHEN both execute
- THEN one MUST return 201 linked and the other MUST return 409

#### Scenario: Filter by estado returns correct subset

- GIVEN 3 anticipos: PENDIENTE_DESCUENTO, DESCONTADO, ANULADO for same socia
- WHEN GET /finanzas/anticipos?socia_id={id}&estado=PENDIENTE_DESCUENTO
- THEN MUST return exactly 1 row

#### Scenario: ANULADO cannot be discounted

- GIVEN anticipo in ANULADO
- WHEN liquidacion tries to include it
- THEN MUST return 422 or 409 and MUST NOT link
