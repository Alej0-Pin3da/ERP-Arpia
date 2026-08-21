<script setup lang="ts">
/**
 * Inventario view (PR9, spec MOD-4 + ui-mantenimiento PR1 T6).
 *
 * Two tabs:
 *  - Insumos: server-side paginated GET /insumos — `nombre_categoria` is
 *    JOINED SERVER-SIDE (no client join), quantities/costs render es-CO and
 *    rows below their minimum are highlighted (stockSeverity, dashboard
 *    pattern). Toolbar: global q + categoria_id filter (server-side, reset to
 *    page 1). The create/edit form + Editar/Eliminar actions are ADMIN ONLY.
 *    **Migrated (UX slice 1): Insumos uses usePaginatedList + EmptyState /
 *    LoadingSkeleton / ErrorState (reference example for other views).**
 *  - Compras: server-side paginated GET /compras-insumos with q +
 *    insumo_id filters. POST runs the WAC service server-side
 *    (updates stock/cost), so a successful compra refreshes BOTH tabs.
 *
 * Lookup joins (ComprasForm options, filter select, compra name join) fetch
 * the full insumos set via src/api/lookups (limit:1000 stop-gap, design D3).
 */
import { computed, onMounted, ref } from 'vue'

import { comprasApi, insumosApi } from '@/api/endpoints'
import { fetchCategoriasLookup, fetchInsumosLookup } from '@/api/lookups'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ComprasForm from '@/components/inventario/ComprasForm.vue'
import ComprasTable from '@/components/inventario/ComprasTable.vue'
import InsumoForm from '@/components/inventario/InsumoForm.vue'
import InsumosTable from '@/components/inventario/InsumosTable.vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Select from 'primevue/select'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import { usePaginatedList } from '@/composables/usePaginatedList'
import { useAuthStore } from '@/stores/auth'
import { confirmAction } from '@/utils/confirm'
import { buildListParams } from '@/utils/pagination'
import { showToast } from '@/utils/toast'
import {
  buildCompraRows,
  type CompraInsumoCreate,
  type InsumoCreate,
  type InsumoUpdate,
} from '@/utils/inventario'
import type { CategoriaInsumoRead, CompraInsumoRead, InsumoRead } from '@/types/api.d'

const auth = useAuthStore()

/** MOD-4: compras register is operador+; insumo master is admin only. */
const canRegister = computed(() => auth.role === 'admin' || auth.role === 'operador')
const canManage = computed(() => auth.role === 'admin')

const activeTab = ref('insumos')
const loading = ref(false)
const error = ref<string | null>(null)

// --- insumos table: via usePaginatedList (UX slice 1 reference) ---------------
const insumosList = usePaginatedList<InsumoRead>((params) => insumosApi.list(params), {
  pageSize: 20,
  initialFilters: { categoria_id: null },
  debounceMs: 300,
})

// Proxy for toolbar Select v-model (Select expects number|null bound)
const filterCategoriaId = computed<number | null>({
  get: () => (insumosList.filters.value.categoria_id as number | null) ?? null,
  set: (v: number | null) => {
    insumosList.filters.value.categoria_id = v
  },
})

// --- compras table: server-side pagination + filters -----------------------
const compras = ref<CompraInsumoRead[]>([])
const comprasTotal = ref(0)
const comprasPage = ref(1)
const comprasPageSize = ref(20)
const compraQ = ref('')
/** Optional GET /compras-insumos?insumo_id filter (clearable select). */
const filterInsumoId = ref<number | null>(null)
const comprasSortBy = ref<string | null>(null)
const comprasSortOrder = ref<'asc' | 'desc' | null>(null)

// --- lookups (full sets via src/api/lookups, limit:1000 stop-gap) -----------
const insumosLookup = ref<InsumoRead[]>([])
const categorias = ref<CategoriaInsumoRead[]>([])

/** Joined compra rows: insumo name + client-computed costo_total, newest first. */
const compraRows = computed(() => buildCompraRows(compras.value, insumosLookup.value))

const savingCompra = ref(false)
const savingInsumo = ref(false)
const editingInsumo = ref<InsumoRead | null>(null)

/** T8/FE-DLG-1: the forms live in PrimeVue Dialogs at the usage site. */
const insumoDialogVisible = ref(false)
const comprasDialogVisible = ref(false)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    // Insumos paginated via composable (keeps its own loading/error but we
    // await it here for the initial joint load to satisfy tests).
    const [, comprasPage_, categoriasList, insumosLookup_] = await Promise.all([
      insumosList.load(),
      comprasApi.list(
        buildListParams({
          page: comprasPage.value,
          pageSize: comprasPageSize.value,
          filtros: { insumo_id: filterInsumoId.value },
          q: compraQ.value,
          sortBy: comprasSortBy.value ?? undefined,
          sortOrder: comprasSortOrder.value ?? undefined,
        }),
      ),
      // Categoria options only feed the admin-only form — skip for other roles.
      canManage.value ? fetchCategoriasLookup().then((items) => ({ items, total: items.length })) : Promise.resolve({ items: [] as CategoriaInsumoRead[], total: 0 }),
      // D3: join fetches keep the full set (no pagination on lookups).
      fetchInsumosLookup().then((items) => ({ items, total: items.length })),
    ])
    compras.value = comprasPage_.items
    comprasTotal.value = comprasPage_.total
    categorias.value = categoriasList.items
    insumosLookup.value = insumosLookup_.items
    // Propagate insumosList error to global error for the header Message fallback
    if (insumosList.error.value) error.value = insumosList.error.value
  } catch {
    error.value = 'No se pudo cargar la información del inventario. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** Surface the server validation detail (400/404/409) when present. */
function serverDetail(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const data = (err as { response?: { data?: unknown } }).response?.data
    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof (data as { detail: unknown }).detail === 'string'
    ) {
      return (data as { detail: string }).detail
    }
  }
  return null
}

/** FE-2: every filter/busqueda change resets to page 1 and refetches. */
function onInsumosSearch(): void {
  // q is already bound via v-model to insumosList.q; force immediate load
  // (bypass the 300ms debounce for explicit Enter/search).
  void insumosList.load()
}

function onInsumosFilterChange(): void {
  // Toolbar Select changed — delegate to composable (resets to page 1)
  insumosList.onFilterChange({ categoria_id: filterCategoriaId.value ?? null })
  // Keep lookup-dependent compras in sync only for insumos tab side-effects:
  // the joint load also refreshes compras/lookups, so trigger full reload.
  // But for filter-only we can just let the composable reload insumos;
  // to keep test expectations (full Promise.all on filter), reload lookups too.
  // Simpler: reload via full load() after the composable's own load — however
  // onFilterChange already called load(), so we avoid double. For now the
  // composable's load suffices for insumos; refresh lookups lazily on create.
  // To keep existing test (expects list called with new filter), the composable
  // already did it. No extra work.
}

function onComprasSearch(): void {
  comprasPage.value = 1
  load()
}

function onComprasFilterChange(): void {
  comprasPage.value = 1
  load()
}

/** Paginator @page (insumos): delegate to composable. */
function onInsumosPage(e: { first: number; rows: number }): void {
  insumosList.onPage(e)
}

/** Paginator @page (compras): recompute the 1-based page from first index. */
function onComprasPage(e: { first: number; rows: number }): void {
  comprasPage.value = Math.floor(e.first / e.rows) + 1
  load()
}

/** Header column filter (InsumosTable) maps into the composable filters. */
function onInsumosTableFilterChange(filters: { categoria_id?: number | null }): void {
  insumosList.onFilterChange({ categoria_id: filters.categoria_id ?? null })
}

/** Header column filter (ComprasTable) maps into the insumo ref. */
function onComprasTableFilterChange(filters: { insumo_id?: number | null }): void {
  filterInsumoId.value = filters.insumo_id ?? null
  onComprasFilterChange()
}

/** Server-side column sort (insumos): delegate to composable. */
function onInsumosTableSortChange(sort: { prop: string; order: 'asc' | 'desc' | null }): void {
  insumosList.onSort(sort)
}

/** Server-side column sort (compras): reset to page 1; null clears the sort. */
function onComprasTableSortChange(sort: { prop: string; order: 'asc' | 'desc' | null }): void {
  comprasSortBy.value = sort.order === null ? null : sort.prop
  comprasSortOrder.value = sort.order
  onComprasFilterChange()
}

/** MOD-4: POST the compra — the WAC service updates stock/cost server-side,
 *  so the refresh reloads BOTH the compras list and the insumos list. */
async function onCreateCompra(payload: CompraInsumoCreate): Promise<void> {
  savingCompra.value = true
  try {
    await comprasApi.create(payload)
    showToast('success', 'Compra registrada correctamente')
    comprasDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo registrar la compra. Verifica los datos e inténtalo de nuevo.')
  } finally {
    savingCompra.value = false
  }
}

/** MOD-4: admin — POST the insumo master row. */
async function onCreateInsumo(payload: InsumoCreate): Promise<void> {
  savingInsumo.value = true
  try {
    await insumosApi.create(payload)
    showToast('success', 'Insumo creado correctamente')
    insumoDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo crear el insumo.')
  } finally {
    savingInsumo.value = false
  }
}

function onEditInsumo(row: InsumoRead): void {
  editingInsumo.value = row
  insumoDialogVisible.value = true
}

/** T8: one @submit entry — route create vs edit by the dialog mode. */
function submitInsumo(payload: InsumoCreate | InsumoUpdate): void {
  if (editingInsumo.value === null) {
    void onCreateInsumo(payload as InsumoCreate)
  } else {
    void onUpdateInsumo(payload as InsumoUpdate)
  }
}

/** FE-DLG-1: the toolbar button opens the dialog in create mode. */
function openCreateInsumo(): void {
  editingInsumo.value = null
  insumoDialogVisible.value = true
}

/** FE-DLG-1: the toolbar button opens the compras dialog in create mode. */
function openCreateCompra(): void {
  comprasDialogVisible.value = true
}

/** FE-DLG-2/3: closing without saving discards the edit prefill. */
function resetInsumoDialog(): void {
  editingInsumo.value = null
}

/** MOD-4: admin — PUT the insumo master row, then back to the create form. */
async function onUpdateInsumo(payload: InsumoUpdate): Promise<void> {
  if (editingInsumo.value === null) return
  savingInsumo.value = true
  try {
    await insumosApi.update({ insumo_id: editingInsumo.value.id }, payload)
    showToast('success', 'Insumo actualizado correctamente')
    insumoDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo actualizar el insumo.')
  } finally {
    savingInsumo.value = false
  }
}

/** MOD-4: admin — delete after a confirm dialog; DELETE answers 204. */
async function onDeleteInsumo(row: InsumoRead): Promise<void> {
  const choice = await confirmAction({
    message: `¿Eliminar el insumo "${row.nombre}"?`,
    header: 'Confirmar eliminación',
    acceptLabel: 'Eliminar',
    rejectLabel: 'Cancelar',
  })
  if (choice !== 'accept') return // cancelled
  try {
    await insumosApi.delete({ insumo_id: row.id })
    showToast('success', 'Insumo eliminado correctamente')
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo eliminar el insumo.')
  }
}

onMounted(load)
</script>

<template>
  <section class="inventario">
    <header class="inventario-header">
      <h2>Inventario</h2>
      <Button :loading="loading || insumosList.loading.value" data-test="refresh-inventario" @click="load">Actualizar</Button>
    </header>

    <div v-if="error || insumosList.error.value" class="inventario-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error ?? insumosList.error.value }}</Message>
    </div>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="insumos">Insumos</Tab>
        <Tab value="compras">Compras</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="insumos">
        <div class="insumo-toolbar">
          <InputText
            v-model="insumosList.q.value"
            placeholder="Buscar insumo…"
            data-test="insumo-search"
            class="insumo-search"
            @keyup.enter="onInsumosSearch"
          />
          <Select
            v-model="filterCategoriaId"
            :options="categorias"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Filtrar por categoría"
            filter
            :show-clear="true"
            data-test="insumo-categoria-filter"
            class="insumo-categoria-filter"
            @change="onInsumosFilterChange"
          />
          <Button v-if="canManage" data-test="nuevo-insumo" @click="openCreateInsumo">
            Nuevo insumo
          </Button>
        </div>

        <LoadingSkeleton v-if="insumosList.loading.value && insumosList.items.value.length === 0" :rows="5" :columns="6" />
        <ErrorState
          v-else-if="insumosList.error.value"
          :message="insumosList.error.value"
          @retry="insumosList.load"
        />
        <EmptyState
          v-else-if="!insumosList.loading.value && insumosList.items.value.length === 0"
          icon="pi pi-inbox"
          title="Sin insumos registrados"
          description="No se encontraron insumos con los filtros actuales."
          action-label="Recargar"
          @action="insumosList.load"
        />
        <template v-else>
          <div class="inventario-table-wrap">
            <InsumosTable
              :rows="insumosList.items.value"
              :loading="insumosList.loading.value"
              :categorias="categorias"
              :can-edit="canManage"
              @edit="onEditInsumo"
              @delete="onDeleteInsumo"
              @filter-change="onInsumosTableFilterChange"
              @sort-change="onInsumosTableSortChange"
            />
          </div>
          <Paginator
            class="tabla-paginacion"
            :total-records="insumosList.total.value"
            :rows="insumosList.pageSize.value"
            :first="(insumosList.page.value - 1) * insumosList.pageSize.value"
            template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
            @page="onInsumosPage"
          />
        </template>

        <Dialog
          v-model:visible="insumoDialogVisible"
          :header="editingInsumo === null ? 'Crear insumo' : 'Editar insumo'"
          modal
          position="top"
          :style="{ width: '90vw', maxWidth: '720px' }"
          :dismissable-mask="false"
          :close-on-escape="!savingInsumo"
          :closable="!savingInsumo"
          @after-hide="resetInsumoDialog"
        >
          <InsumoForm
            v-if="insumoDialogVisible"
            :mode="editingInsumo === null ? 'create' : 'edit'"
            :initial="editingInsumo"
            :categorias="categorias"
            :saving="savingInsumo"
            @submit="submitInsumo"
          />
        </Dialog>
      </TabPanel>

      <TabPanel value="compras">
        <div class="compras-filtro">
          <InputText
            v-model="compraQ"
            placeholder="Buscar por insumo…"
            data-test="compra-search"
            class="compra-search"
            @keyup.enter="onComprasSearch"
          />
          <Select
            v-model="filterInsumoId"
            :options="insumosLookup"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Filtrar por insumo"
            filter
            :show-clear="true"
            data-test="compra-filter-select"
            class="compra-filter-select"
            @change="onComprasFilterChange"
          />
          <Button v-if="canRegister" data-test="nueva-compra" @click="openCreateCompra">
            Nueva compra
          </Button>
        </div>

        <div class="inventario-table-wrap">
          <ComprasTable
            :rows="compraRows"
            :loading="loading"
            :insumos="insumosLookup"
            @filter-change="onComprasTableFilterChange"
            @sort-change="onComprasTableSortChange"
          />
        </div>
        <Paginator
          class="tabla-paginacion"
          :total-records="comprasTotal"
          :rows="comprasPageSize"
          :first="(comprasPage - 1) * comprasPageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="onComprasPage"
        />

        <Dialog
          v-model:visible="comprasDialogVisible"
          header="Nueva compra"
          modal
          position="top"
          :style="{ width: '90vw', maxWidth: '720px' }"
          :dismissable-mask="false"
          :close-on-escape="!savingCompra"
          :closable="!savingCompra"
        >
          <ComprasForm
            v-if="comprasDialogVisible"
            :insumos="insumosLookup"
            :saving="savingCompra"
            @submit="onCreateCompra"
          />
        </Dialog>
      </TabPanel>
      </TabPanels>
    </Tabs>
  </section>
</template>

<style scoped>
.inventario-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.inventario-header h2 {
  margin: 0;
}

.inventario-error {
  margin-bottom: 1rem;
}

.insumo-toolbar,
.compras-filtro {
  display: flex;
  gap: 0.75rem;
  max-width: 42rem;
  margin-bottom: 1rem;
}

.insumo-search,
.compra-search {
  width: 14rem;
}

.insumo-categoria-filter,
.compra-filter-select {
  width: 12rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}

.inventario-table-wrap {
  width: 100%;
  overflow-x: auto;
  overscroll-behavior-x: contain;
}

@media (max-width: 767px) {
  .inventario-header {
    align-items: flex-start;
    gap: 0.75rem;
  }

  .inventario-header h2 {
    font-size: 1.35rem;
  }

  .insumo-toolbar,
  .compras-filtro {
    max-width: none;
    flex-direction: column;
    gap: 0.5rem;
  }

  .insumo-search,
  .compra-search,
  .insumo-categoria-filter,
  .compra-filter-select,
  .insumo-toolbar :deep(.p-button),
  .compras-filtro :deep(.p-button) {
    width: 100%;
  }

  .tabla-paginacion {
    justify-content: center;
    overflow-x: auto;
  }
}
</style>
