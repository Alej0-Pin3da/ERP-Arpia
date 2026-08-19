# Spec: Frontend Migration Element Plus → PrimeVue 4.5.5 (MIT)

## Purpose

Migrate the ERP-Arpia frontend UI framework from Element Plus 2.9.3 (full-bundle global registration) to PrimeVue 4.5.5 (exact pin, last MIT) with per-component imports, preserving all user-observable behavior, theme, locale, and test coverage. **Capabilities: None** — a pure framework refactor. No existing capability spec is modified: all 7 main specs (`openspec/specs/*`) are backend domains (wac-engine, ventas-variantes, productos, migracion-catalogos, costos-produccion, bom, compras-insumos). This standalone document records the migration requirements, preservation invariants, and success criteria; there is no delta target to merge at archive.

## Requirements

### Requirement: MIG-1 — Frontend-only migration

The system SHALL migrate the frontend to `primevue@4.5.5`, `@primeuix/themes` (v2.x), and `primeicons`. The change MUST NOT modify backend code, API contracts, or data semantics, and MUST ship in 6 slices (0 foundations, 1 tables, 2 1:1 components, 3 no-clean-equivalent, 4 messages+theme, 5 cleanup), each independently mergeable with a green suite.

#### Scenario: Backend isolation

- GIVEN the change is complete
- WHEN the diff is inspected
- THEN no file outside `frontend/` is modified

### Requirement: MIG-2 — Hybrid dual-registration

The system SHALL keep Element Plus registered through slice 4 while PrimeVue is registered alongside; Element Plus and its CSS SHALL be fully removed in slice 5. Components SHALL be imported per-file (no full-bundle global registration).

#### Scenario: Transition window

- GIVEN slices 0–4 merged
- WHEN the app boots
- THEN both frameworks render; after slice 5, zero `el-*`/`element-plus` references remain

### Requirement: MIG-3 — Build size budget (Q7 resolved)

The build size SHALL be ≤ slice-0 baseline +10%. Baseline SHALL be measured in slice 0; the final comparison in slice 5.

#### Scenario: Budget check

- GIVEN slice-0 baseline B and slice-5 build size S
- WHEN the final build is measured
- THEN S ≤ B × 1.10

### Requirement: MIG-4 — Suite green per slice

The vitest suite (32 specs) SHALL pass at every slice. Specs SHALL drop `plugins: [ElementPlus]`, mount with `attachTo` for Teleport components (Dialog/Toast/ConfirmDialog), and migrate `.el-*` selectors to `.p-*` in lockstep with each slice.

#### Scenario: Slice-0 pilot

- GIVEN slice 0 merged
- WHEN `npm test` runs in `frontend/`
- THEN all specs pass

### Requirement: BEH-1 — Filter/sort semantics parity (Q6 resolved: preserve current semantics)

Server-side filter/sort behavior SHALL be preserved. Header funnels emit the single selected value; empty/cleared emits null; sort emits `asc`/`desc`/`null`. The typed `filter-change`/`sort-change` emit contract SHALL remain unchanged, with DataTable in `lazy` mode wiring `@filter`/`@sort` to the same view handlers. `parseColumnFilter` semantics (first selected value, `{text,value}` unwrap, empty → null) SHALL be preserved via the slice-1 adapter.

#### Scenario: Funnel select

- GIVEN the user selects "web" in the Canal funnel
- WHEN the table emits the filter change
- THEN `canal_venta` resolves to `"web"` and the view refetches with that server-side filter

#### Scenario: Funnel cleared

- GIVEN the user clears the Estado funnel
- WHEN the table emits the filter change
- THEN `estado` resolves to `null` and the view refetches without the filter

### Requirement: BEH-2 — 403 toast preserved

The `client.ts` axios response interceptor SHALL still surface `FORBIDDEN_MESSAGE` as an error toast on HTTP 403 (via the Toast singleton service) and SHALL still reject the promise so callers react.

#### Scenario: Forbidden request

- GIVEN a user triggers an action their role cannot perform
- WHEN the API returns 403
- THEN an error toast with the forbidden message appears AND the promise rejects

### Requirement: BEH-3 — Login validation parity

LoginView SHALL keep equivalent validation: email required + email-type, password required, blur-triggered, with messages identical to today ("Ingrese su correo electrónico", "El correo no es válido", "Ingrese su contraseña"), submit blocked while invalid, inline error alert for failed login (401 vs connection), loading state. No new validation dependency.

#### Scenario: Invalid email

- GIVEN the email field contains "abc"
- WHEN the user blurs and submits
- THEN "El correo no es válido" shows inline AND no request is sent

### Requirement: BEH-4 — Dark theme visual parity

The dark editorial theme SHALL visually match the current look. The custom `definePreset(Aura)` SHALL map the 110 `--el-*` tokens onto `--p-*` tokens, driven by existing `--arpia-*` brand vars (lavender primary, gold accents, surfaces, gradients), with class-selector dark mode. Visual parity SHALL be QA'd in slice 4.

#### Scenario: Theme QA

- GIVEN slice 4 merged
- WHEN main views render in dark mode
- THEN surfaces, text, borders, and gold/lavender accents match the pre-migration look

### Requirement: BEH-5 — Messages and confirmations parity

All `ElMessage` (104 calls: 36 error / 35 success / 33 warning) and `ElMessageBox` (18 refs) SHALL be replaced by Toast/ConfirmDialog services preserving severity and message content. Hosts SHALL be mounted at app root so the non-component `client.ts` interceptor can use them.

#### Scenario: Success message

- GIVEN a user saves a record
- WHEN the save succeeds
- THEN a success toast with the same text as today appears

### Requirement: BEH-6 — Workflows unaffected

Row expansion with nested detail tables (VentasTable expand → detalles), product/variant selection, gift marking, empty states (`el-empty` → `#empty` template), and loading states (`v-loading` → DataTable `:loading`) SHALL behave as today.

#### Scenario: Expand row

- GIVEN a venta row with detalles
- WHEN the user expands the row
- THEN the nested detail table renders with formatted cantidad/precio and row actions work

### Requirement: BEH-7 — es-CO locale parity

The PrimeVue locale SHALL be an authored es-CO plain object covering paginator, datepicker, filter, and aria keys, matching the Spanish labels users see with Element Plus's es locale.

#### Scenario: Paginator labels

- GIVEN a paginated table in Spanish
- WHEN the user views the paginator
- THEN labels match the current es-CO wording

## Open design questions (noted for design phase — not decided here)

Q1 16px vs `-compat` 14px baseline; Q2 Aura vs Lara base; Q3 `el-container` → CSS grid layout (visual acceptance covered by BEH-4 QA); Q4 Toast/ConfirmDialog host placement + singleton API shape; Q5 es-CO key inventory (coverage by BEH-7).

## Success Criteria

- Suite green at every slice; 21 `.el-*` selector specs migrated
- Zero `el-*`/`element-plus` references after slice 5
- Dark editorial theme visually matches (slice-4 QA)
- 403 Toast message works from `client.ts`
- Build size ≤ baseline +10% (slice 0 measure, slice 5 verify)
- No backend changes (diff isolated to `frontend/`)