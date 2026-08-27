# Delta for finanzas-liquidaciones

## ADDED Requirements

### Requirement: LIQ-1 — Liquidacion Header + Distribucion Child Model

The system MUST create `liquidaciones` (header) and `liquidacion_distribucion` (child) per ERP-V4 §6.4, replacing simulated `Movimientos_Financieros.liquidacion_id`. Header MUST have `codigo VARCHAR(12) UNIQUE LIQ-YYYY-NN` (auto, sequential/year), `periodo VARCHAR(20)`, `fecha_cierre DATE`, six `NUMERIC(12,2)` totals (`total_ventas_brutas`, `costo_taller_insumos`, `gastos_operativos`, `utilidad_neta_total`, `fondo_reinversion_monto`, `utilidad_repartible`), `estado CHECK BORRADOR|APROBADA|PAGADA DEFAULT BORRADOR`, `observaciones TEXT`, `creado_en/actualizado_en TIMESTAMPTZ`. Child MUST have `liquidacion_id FK CASCADE`, `socia_id FK CASCADE`, `porcentaje NUMERIC(5,2)`, `monto_bruto`, `deduccion_anticipos DEFAULT 0`, `monto_neto_pagar` (all `NUMERIC(12,2)`), `estado_pago CHECK PENDIENTE|PAGADO|RETENIDO`. Pair `(liquidacion_id, socia_id)` MUST be unique. System MUST NOT use JSONB.

#### Scenario: Create generates header + per-socia rows

- GIVEN active socias Fondo 40/Margarita 30/Valqui 30 and utilidad_repartible 100000
- WHEN POST /finanzas/liquidaciones with periodo 2026-07 and six totals
- THEN header MUST have codigo `LIQ-2026-\d{2}` and 3 child rows 40000/30000/30000 in BORRADOR

#### Scenario: Duplicate codigo rejected

- GIVEN LIQ-2026-01 exists
- WHEN second POST reuses that codigo or concurrent generation collides
- THEN MUST return 409 and MUST NOT create duplicate

#### Scenario: Delete BORRADOR cascades children

- GIVEN liquidacion BORRADOR with 3 distribucion rows
- WHEN DELETE /finanzas/liquidaciones/{id}
- THEN header and children MUST be removed; GET MUST return 404

### Requirement: LIQ-2 — State Machine BORRADOR → APROBADA → PAGADA

System MUST enforce linear `BORRADOR → APROBADA → PAGADA` via `VARCHAR CHECK` + StrEnum `LiquidacionEstado` + transition map (finanzas.py `DocumentState` pattern, distinct enum). Only those two transitions are valid; any other MUST return 422. `PAGADA` is terminal (no edits to totals/distribucion, no further transitions). Edits to totals/distribucion MUST be allowed only in `BORRADOR`.

#### Scenario: Valid progression succeeds

- GIVEN liquidacion in BORRADOR
- WHEN PATCH to APROBADA then to PAGADA
- THEN both MUST return 200 and final estado MUST be PAGADA

#### Scenario: Skip or revert rejected

- GIVEN liquidacion in BORRADOR
- WHEN PATCH directly to PAGADA
- THEN MUST return 422 and estado MUST remain BORRADOR

#### Scenario: Terminal PAGADA rejects further transitions

- GIVEN liquidacion in PAGADA
- WHEN PATCH to BORRADOR or APROBADA
- THEN MUST return 422

### Requirement: LIQ-3 — Payload-as-Source, Audit Drift, Fondo 40% and Deduction

System MUST treat payload totals as source of truth. On create/update in BORRADOR it SHOULD validate `utilidad_neta_total == total_ventas_brutas - costo_taller_insumos - gastos_operativos`; mismatch SHOULD return 422. It SHOULD audit by summing `Movimientos_Financieros` for `periodo`; if payload drifts >5% vs that sum, it MUST still persist but SHOULD include `warnings: ["drift >5% vs movimientos"]` (no hard reject). Distribucion MUST be computed over all `activo=true` socias including fondo; `fondo_reinversion_monto` MUST equal 40% of `utilidad_neta_total` when `es_fondo_taller` exists. Each row: `monto_bruto = utilidad_repartible * porcentaje/100`; `monto_neto = monto_bruto - deduccion_anticipos` (sum of `PENDIENTE_DESCUENTO` anticipos at creation, see ANT-2).

#### Scenario: Drift warning without blocking

- GIVEN movimientos sum 100000 but payload declares 120000 (>5%)
- WHEN POST liquidacion for that periodo
- THEN MUST persist 120000 and SHOULD include drift warning

#### Scenario: Correct split with fondo and anticipo deduction

- GIVEN Fondo 40/Margarita 30/Valqui 30, utilidad_repartible 100000, Margarita has pending anticipo 5000
- WHEN liquidacion is created
- THEN distribucion MUST be Fondo 40000/0/40000, Margarita 30000/5000/25000, Valqui 30000/0/30000

#### Scenario: Inactive socia excluded

- GIVEN 3 active socias and 1 with `activo=false`
- WHEN liquidacion is created
- THEN distribucion MUST contain exactly 3 rows
