# Design: Frontend Migration Element Plus → PrimeVue 4.5.5 (MIT)

## Technical Approach

Frontend-only framework swap executed as 6 stacked slices with hybrid dual-registration (EP registered through slice 4, PrimeVue alongside from slice 0). Per-component imports (no full-bundle). Custom `definePreset(AuraCompat)` maps the current `--el-*` editorial palette onto `--p-*` tokens, driven by the existing `--arpia-*` brand vars (BEH-4). Server-side filter/sort semantics preserved verbatim via a slice-1 adapter over DataTable `lazy` mode (BEH-1). Toast/ConfirmDialog singleton hosts at the app root so the non-component `client.ts` 403 interceptor keeps working (BEH-2/BEH-5). Test suite migrates in lockstep: drop `plugins: [ElementPlus]`, `attachTo` for Teleport, `.el-*` → `.p-*` selectors (MIG-4). Build baseline measured in slice 0, verified ≤ +10% in slice 5 (MIG-3).

## Architecture Decisions

| # | Decision | Choice | Alternatives | Rationale |
|---|---|---|---|---|
| D1 | Font baseline (Q1) | **Keep root 16px + `AuraCompat` preset** (`@primeuix/themes/aura-compat`) | 14px root + standard Aura; 16px root + standard Aura | `body{font-size:16px}` (main.css:168) but EP components render at EP's internal 14px base (app never overrides `--el-font-size-base`). AuraCompat is calibrated for a 14px root → components render at EP-era 14px density under the untouched 16px root. Changing root to 14px would break the rem-based editorial typography (headings, `1.25rem` paddings); standard Aura at 16px root renders visibly larger than today. AuraCompat = BEH-4 parity with zero typography disruption |
| D2 | Preset base (Q2) | **Aura (via `AuraCompat`)** | Lara, Nora, Material | App is a minimal dark-editorial look (serif Lora body, lavender `#8c6ca1`, gold accents, 4–8px radii). Aura is PrimeTek's modern minimal token set with clean dark `colorScheme` structure and surface tokens that map 1:1 onto `--arpia-dark*` surfaces; Lara is Bootstrap-flavored legacy styling. Exploration recommendation: Aura |
| D3 | Layout (Q3) | **CSS grid shell** in `AppLayout.vue` via `grid-template-areas` | Flexbox columns; keep `el-container` | 3-region shell (aside 220px / header / main) is exactly one grid. CSS: `.app-layout{display:grid;grid-template-columns:220px 1fr;grid-template-rows:auto 1fr;grid-template-areas:"aside header" "aside main";min-height:100vh}` with `.app-layout__aside/header/main{grid-area:...}`. Scoped styles already own surfaces/borders — only the 3 wrapper tags change. Visual acceptance: BEH-4 slice-4 QA (same 220px sidebar, header height, main scroll) |
| D4 | Toast/Confirm hosts (Q4) | **Hosts in `App.vue`** (wraps router-view) + module singletons `src/utils/toast.ts`, `src/utils/confirm.ts` | Hosts in AppLayout.vue | App.vue is the true app root — hosts exist for the whole app lifetime including /login (403 can fire pre-shell). AppLayout.vue mounts only after auth. Singleton: App.vue setup captures `useToast()`/`useConfirm()` into module vars; `client.ts` imports `showToast()` only |
| D5 | Locale (Q5) | **Authored es-CO plain object** (`src/utils/locales/es-CO.ts`), `app.use(PrimeVue,{locale:esCO})` | `element-plus/es/locale/lang/es` reuse (impossible — different key surface) | PrimeVue has no bundled es locale; key surface (paginator/datepicker/aria/filter) differs from EP's `el.*` shape. Values match the EP es labels users see today (pagination "Total {total}" → `currentPageReportTemplate:'Total {totalRecords}'`, "Ir a" → `jumpToPageInputLabel`) |
| D6 | Filter/sort adapter (Q6, BEH-1) | **`parseColumnFilter` unchanged**; add `parsePrimeVueFilters` (constraint→array unwrap) + `parsePrimeVueSort` (1/-1→asc/desc/null) in `table-filters.ts` | Rewrite `parseColumnFilter`; inline handlers per table | DataTable `@filter` emits `{filters: Record<col,{value,matchMode} | [...]>}`; `parseColumnFilter` consumes `unknown[]`. The adapter normalizes the new payload back to the exact array shape, so first-selected-value, `{text,value}` unwrap, and empty→null semantics survive untouched for all 9 callers |
| D7 | LoginView validation (BEH-3) | **Manual validation** with inline error divs (no el-form/el-form-item/rules) | VeeValidate dependency | Matches the other 13 manual forms; zero new deps. Blur-triggered checks for email required/type + password required with the exact current messages; submit blocked while invalid; `el-alert` → Message severity error for the 401/connection alert |
| D8 | v-tooltip | **Tooltip directive** (`primevue/tooltip`, `app.directive('tooltip', Tooltip)`) | Component wrapper | VentasTable gift button: `v-tooltip="{value:'Marcar como regalo', position:'top'}"`, aria-label kept on the button (ventas-table.spec covers it) |

## Data Flow

```
Filter:  DataTable(lazy) --@filter {filters:Record<col,{value,matchMode}>}-->
         parsePrimeVueFilters → parseColumnFilter → emit('filter-change',{col:value|null})
         → view handler → buildListParams → GET /ventas?canal_venta=web (page reset 1)

Sort:    DataTable --@sort {sortField,sortOrder}--> parsePrimeVueSort
         → emit('sort-change',{prop,order:'asc'|'desc'|null}) → buildListParams sort_by/sort_order

403:     axios response interceptor (client.ts) --403--> showToast('error',FORBIDDEN_MESSAGE)
         → toast singleton → <Toast/> host in App.vue → reject(error) [promise contract kept]

Confirm: view --confirmAction({message,header,...})--> useConfirm.require
         → <ConfirmDialog/> host → resolves 'accept'|'reject' (replaces ElMessageBox await/catch)
```

## File Changes

| File | Action | Description |
|---|---|---|
| `frontend/package.json` | Modify | Add `primevue@4.5.5` (exact), `@primeuix/themes@^2`, `primeicons` |
| `frontend/src/main.ts` | Modify | S0: dual registration (`app.use(PrimeVue,{theme:{preset:ArpiaPreset,options:{darkModeSelector:'html'}},locale:esCO})` + ToastService + ConfirmationService + Tooltip directive); S5: remove EP |
| `frontend/src/styles/main.css` | Modify | S4: `--el-*` palette + `.el-*` overrides → `--p-*` via preset tokens; keep `--arpia-*` brand vars as the single source |
| `frontend/src/styles/arpia-preset.ts` (new) | Create | S0 skeleton → S4 full: `definePreset(AuraCompat, {...})` mapping `--arpia-*`/`--el-*` values onto semantic/component tokens; dark scheme only |
| `frontend/src/utils/locales/es-CO.ts` (new) | Create | S0: authored locale object (~40 keys, D5) |
| `frontend/src/utils/toast.ts` (new) | Create | S0: `setToastInstance`/`showToast(severity,summary,detail,life?)` singleton |
| `frontend/src/utils/confirm.ts` (new) | Create | S4: `setConfirmInstance`/`confirmAction(opts): Promise<'accept'\|'reject'>` |
| `frontend/src/utils/table-filters.ts` | Modify | S1: add `parsePrimeVueFilters`, `parsePrimeVueSort`; `parseColumnFilter` untouched |
| `frontend/src/api/client.ts` | Modify | S4: `ElMessage.error` → `showToast('error','Acceso denegado',FORBIDDEN_MESSAGE)`; promise reject unchanged |
| `frontend/src/App.vue` | Modify | S0: mount `<Toast position="top-right"/>` + `<ConfirmDialog/>` beside `<router-view/>`; capture singletons in setup |
| `frontend/src/layouts/AppLayout.vue` | Modify | S3: `el-container/el-header/el-aside/el-main` → CSS grid shell; el-tag→Tag, el-button→Button |
| `frontend/src/components/layout/SidebarMenu.vue` | Modify | S3: `el-menu/el-menu-item` → flat `<nav>` + `<router-link>` list (role menu is flat; active class from `route.path`) |
| `frontend/src/views/LoginView.vue` | Modify | S3: manual validation + Message alert; InputText/Password/Button |
| `frontend/src/components/ventas/VentasTable.vue` | Modify | S1: DataTable lazy, Column expander + `#expansion` nested DataTable, `#empty` template, `:loading`, v-tooltip |
| 42 remaining `.vue` files | Modify | Slices 1–4 per mapping table |
| `frontend/tests/unit/table-filters.spec.ts` | Modify | S1: adapter unit tests (contract below) |
| 31 remaining specs | Modify | Per-slice: drop `plugins:[ElementPlus]`, `attachTo` for Teleport, `.el-*`→`.p-*` |
| `frontend/tests/component/*.spec.ts` | Modify | Pilot S0: `layout.spec.ts` first (Tag/Button in AppLayout) |

## Interfaces / Contracts

```ts
// table-filters.ts (S1 additions; parseColumnFilter signature UNCHANGED)
export interface PrimeVueFilterConstraint { value: unknown; matchMode?: string }
export function parsePrimeVueFilters(filters: Record<string, PrimeVueFilterConstraint | PrimeVueFilterConstraint[]>): Record<string, unknown[]>
//   → [{value:'web'}] → {canal_venta:['web']}; [{value:null}] → {canal_venta:[null]}
export function parsePrimeVueSort(s: { sortField?: string; sortOrder?: number }): { prop: string; order: 'asc' | 'desc' | null }
//   sortOrder 1→'asc', -1→'desc', else null
```

```ts
// toast.ts — module singleton (no Vue imports; works from client.ts)
type ToastSeverity = 'success' | 'info' | 'warn' | 'error'
export function setToastInstance(t: ToastServiceMethods): void
export function showToast(severity: ToastSeverity, summary: string, detail?: string, life = 3000): void
// confirm.ts
export function confirmAction(o: { message: string; header?: string; acceptLabel?: string; rejectLabel?: string }): Promise<'accept' | 'reject'>
```

```ts
// es-CO.ts — ~40 keys, values match current EP es labels (D5)
export const esCO = {
  accept: 'Aceptar', reject: 'Rechazar', cancel: 'Cancelar', clear: 'Limpiar',
  today: 'Hoy', now: 'Ahora',
  dayNames: ['domingo','lunes','martes','miércoles','jueves','viernes','sábado'],
  dayNamesShort: ['dom','lun','mar','mié','jue','vie','sáb'],
  dayNamesMin: ['D','L','M','X','J','V','S'],
  monthNames: ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'],
  monthNamesShort: ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'],
  dateFormat: 'dd/mm/yy', firstDayOfWeek: 0, isRTL: false, ampm: false,
  month: 'Mes', week: 'Semana', day: 'Día', hour: 'Hora', minute: 'Minuto', second: 'Segundo',
  paginator: {
    firstPageLabel: 'Primera página', lastPageLabel: 'Última página',
    nextPageLabel: 'Siguiente página', prevPageLabel: 'Página anterior',
    firstPageLinkLabel: 'Ir a la primera página', lastPageLinkLabel: 'Ir a la última página',
    nextPageLinkLabel: 'Ir a la página siguiente', prevPageLinkLabel: 'Ir a la página anterior',
    jumpToPageDropdownLabel: 'Ir a la página', jumpToPageInputLabel: 'Ir a la página',
    pageLabel: 'Página', rowsPerPageLabel: 'Filas por página', ofLabel: 'de',
    totalRecordsLabel: 'Total', currentPageReportTemplate: 'Total {totalRecords}',
  },
  aria: {
    trueLabel: 'Verdadero', falseLabel: 'Falso', nullLabel: 'No seleccionado',
    star: '1 estrella', stars: '{star} estrellas', selectAll: 'Seleccionar todos',
    unselectAll: 'Deseleccionar todos', close: 'Cerrar', previous: 'Anterior', next: 'Siguiente',
    navigation: 'Navegación', scrollTop: 'Desplazarse arriba',
    moveUp: 'Mover arriba', moveDown: 'Mover abajo', moveLeft: 'Mover izquierda', moveRight: 'Mover derecha',
    select: 'Seleccionar', unselect: 'Deseleccionar', sort: 'Ordenar',
    expand: 'Expandir', collapse: 'Contraer', filter: 'Filtrar',
    filterMatchMode: 'Modo de coincidencia', filterConstraint: 'Restricción de filtro',
    filterOperator: 'Operador de filtro', filterClear: 'Limpiar filtro',
    filterApply: 'Aplicar filtro', filterAdd: 'Agregar filtro',
  },
}
```

## Component Mapping Table

| EP component (count) | PrimeVue target | Import path | Key deltas | Notes |
|---|---|---|---|---|
| el-table (21) | DataTable | `primevue/datatable` | `:data`→`:value`, `@filter-change`→`@filter`(lazy), `@sort-change`→`@sort`, `v-loading`→`:loading`, `type="expand"`→`expander` column | `lazy` + `@filter`/`@sort` wired to existing handlers via adapter |
| el-table-column (107) | Column | `primevue/column` | `prop`/`column-key`→`field`, `#default`→`#body`, `:filters`→`:showFilterMenu`+`filterElement` | expander + `#expansion` for nested tables |
| el-button (67) | Button | `primevue/button` | `type`→`severity` (primary/success/warning/danger), `plain`→`text`, `link`→`link`, `native-type`→`type` | `circle`, `size`, `loading` same |
| el-input (22) | InputText | `primevue/inputtext` | near 1:1 | LoginView password → Password `primevue/password` |
| el-input-number (21) | InputNumber | `primevue/inputnumber` | near 1:1; keydown semantics differ | verify step/min/max |
| el-select (28) | Select | `primevue/select` | `:options`+`optionLabel` or SelectOption children; `clearable`,`filterable` same | toolbar filters + forms |
| el-option (38) | SelectOption | `primevue/selectoption` | `label`/`value` same | dropped when using `:options` |
| el-dialog (12) | Dialog | `primevue/dialog` | `v-model`→`v-model:visible`, `width`→`style`, `@closed` same, `:show-close` | Teleport→body (attachTo in tests) |
| el-tabs (6) | Tabs | `primevue/tabs` | **v4 structure**: `<Tabs v-model:value><TabList><Tab><TabPanels><TabPanel>` | `label`→Tab header, `name`→`value` |
| el-tab-pane (11) | TabPanel | `primevue/tabpanel` | see Tabs | — |
| el-pagination (10) | Paginator | `primevue/paginator` | `:total`→`:totalRecords`, `:page-size`→`:rows`, `:current-page`→`:first`, `@current-change`→`@page{first,rows}` | `template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"` |
| el-tag (11) | Tag | `primevue/tag` | `type`→`severity` (success/danger/warning→warn) | role badge, estado tags |
| el-card (7) | Card | `primevue/card` | near 1:1; `#header`/`#default` | — |
| el-alert (11) | Message | `primevue/message` | `type`→`severity`, `:title`→slot text, `show-icon`, `:closable` | LoginView + view errors |
| el-date-picker (3) | DatePicker | `primevue/datepicker` | locale-driven | es-CO labels via D5 |
| el-skeleton (3) | Skeleton | `primevue/skeleton` | near 1:1 | — |
| el-switch (2) | ToggleSwitch | `primevue/toggleswitch` | near 1:1 | v-model |
| el-progress (1) | ProgressBar | `primevue/progressbar` | `:percentage`→`:value`, `:show-text`→`showValue` | — |
| el-tooltip (1) | v-tooltip directive | `primevue/tooltip` | component→directive: `v-tooltip="{value,position}"` | VentasTable gift button (D8) |
| el-menu (1) | none (nav list) | — | `el-menu router` flat list → `<nav>`+`<router-link>` | SidebarMenu (D3) |
| el-menu-item (1) | none | — | active class from `route.path` | — |
| el-container/header/aside/main (2/1/1/1) | none (CSS grid) | — | `grid-template-areas` shell | AppLayout (D3) |
| el-form (14) / el-form-item (45) | none | — | manual validation + inline error divs | only LoginView used rules (D7) |
| el-row (13) / el-col (37) | none | — | CSS grid / flex rows | view-level layouts |
| el-empty (20) | none | — | DataTable `#empty` template / custom markup | `description` text kept |
| v-loading (17) | none | — | DataTable `:loading`; views: Skeleton/overlay | — |
| ElMessage (104) | Toast service | `primevue/toast` + `primevue/toastservice` | `ElMessage.error/success/warning` → `showToast('error'/'success'/'warn', summary, detail)` | hosts in App.vue (D4) |
| ElMessageBox (18) | ConfirmDialog service | `primevue/confirmdialog` + `primevue/confirmationservice` | `await confirm`/`catch cancel` → `await confirmAction` → `if (choice!=='accept') return` | VentasView anular/regalo etc. |

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | Adapter contract | `table-filters.spec.ts`: `parsePrimeVueFilters` single/multi constraint, `{value:null}`→`[null]`→`null` via parseColumnFilter, `{text,value}` unwrap preserved; `parsePrimeVueSort` 1→asc, -1→desc, 0/undefined→null |
| Unit | toast singleton | `toast` no-op before `setToastInstance`; add calls host-less instance |
| Component | Specs (32) | Drop `plugins:[ElementPlus]`; components resolve from SFC imports; `attachTo: document.body` for Dialog/Toast/ConfirmDialog/DatePicker (Teleport); existing ResizeObserver polyfill in `tests/setup.ts` reused (DataTable needs it); `.el-*`→`.p-*` selectors in lockstep (`.el-table__row`→`.p-datatable-row`, `.el-message`→`.p-toast-message`) |
| Component | Slice-0 pilot | `component/layout.spec.ts` migrates FIRST (Tag/Button in AppLayout + Toast/ConfirmDialog hosts mounted): proves per-component imports, attachTo, and dual-registration coexistence on the smallest surface |
| E2E | Visual parity (BEH-4) | Manual dark-mode QA in slice 4 (main views: tables, dialogs, forms, toasts) — screenshots vs pre-migration |
| Build | Budget (MIG-3) | Slice 0: `vite build` output size = baseline B; slice 5: S ≤ B×1.10 |

Selector migration order per slice: table specs (S1) → form/view specs (S2) → login/layout specs (S3) → message specs (S4) → final cleanup (S5).

## Slice / PR Breakdown (stacked-to-main, auto-chain)

| Slice | PRs | Scope | Verify |
|---|---|---|---|
| 0 Foundations | 1 PR | deps pin; `main.ts` dual registration + PrimeVue config (AuraCompat skeleton, es-CO); Toast/ConfirmDialog hosts in App.vue + toast.ts singleton; `arpia-preset.ts` skeleton; build baseline; pilot `layout.spec.ts` + AppLayout Tag/Button | `npm test` green; build size recorded |
| 1 Tables | 3 PRs: 1a Ventas (VentasTable nested expand + ventas-view + ventas specs), 1b Insumos/Movimientos, 1c Compras | adapter in `table-filters.ts` + unit tests; DataTable/Column/Paginator; `#empty`; `:loading` | `npm test` green per PR |
| 2 1:1 components | 2 PRs: 2a forms batch (InputText/InputNumber/Select/Dialog/Tabs/Skeleton/Card/ToggleSwitch/ProgressBar), 2b tags+buttons+tooltip sweep | remaining `el-*` → `p-*` in views/forms | `npm test` green per PR |
| 3 No-clean-equivalent | 2 PRs: 3a empty/alert/loading sweep, 3b layout + LoginView (CSS grid shell, nav list, manual validation) | el-empty→#empty, el-alert→Message, v-loading→:loading/overlay, AppLayout grid, SidebarMenu nav, LoginView manual rules | `npm test` green per PR |
| 4 Messages + theme | 2 PRs: 4a messages sweep (104 ElMessage + 18 ElMessageBox → services incl. client.ts 403), 4b theme (main.css → full preset tokens + `.el-*` overrides) + visual QA | BEH-2/BEH-5/BEH-4 | `npm test` green; dark-mode QA sign-off |
| 5 Cleanup | 1 PR | remove `element-plus` dep + registration + CSS; strip last `plugins:[ElementPlus]`; lint/typecheck/prettier; final build compare ≤ +10% | `npm test` green; `S ≤ B×1.10` |

## Migration / Rollout

Dual-registration keeps EP functional through slice 4; each PR independently mergeable and revertible. Slice 5 (EP removal) is the only destructive step — gated on full green suite + visual QA sign-off.

## Rollback

- Per-PR revert in the chain: EP still registered and functional until slice 5, so reverting any slice 0–4 PR restores the prior green state (additive changes only).
- Abort = stop the chain at the current head; no cleanup needed (nothing destructive before slice 5).
- Slice 5: revert the single PR restores dual registration; do not merge it without the QA gate.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. (The axios client and router are data-flow consumers, not process boundaries.)

## Open Questions

- None blocking. (Q1–Q7 resolved as D1–D6 + spec; Q8 scope guard enforced in tasks; Q9 budget = MIG-3.)