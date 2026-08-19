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
 *  - Compras: server-side paginated GET /compras-insumos with q +
 *    insumo_id filters. POST runs the WAC service server-side
 *    (updates stock/cost), so a successful compra refreshes BOTH tabs.
 *
 * Lookup joins (ComprasForm options, filter select, compra name join) fetch
 * the full insumos set with limit:1000 against `.items` (design D3) — table
 * views use real pagination, join fetches keep the lookup hack.
 */
import { computed, onMounted, ref } from 'vue'

import { categoriasInsumosApi, comprasApi, insumosApi } from '@/api/endpoints'
import ComprasForm from '@/components/inventario/ComprasForm.vue'
import ComprasTable from '@/components/inventario/ComprasTable.vue'
import InsumoForm from '@/components/inventario/InsumoForm.vue'
import InsumosTable from '@/components/inventario/InsumosTable.vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
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

// --- insumos table: server-side pagination + filters -----------------------
const insumos = ref<InsumoRead[]>([])
const insumosTotal = ref(0)
const insumosPage = ref(1)
const insumosPageSize = ref(20)
const insumoQ = ref('')
const filterCategoriaId = ref<number | null>(null)
const insumosSortBy = ref<string | null>(null)
const insumosSortOrder = ref<'asc' | 'desc' | null>(null)

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

// --- lookups (full sets, limit:1000 — design D3) ---------------------------
const insumosLookup = ref<InsumoRead[]>([])
const categorias = ref<CategoriaInsumoRead[]>([])

/** Joined compra rows: insumo name + client-computed costo_total, newest first. */
const compraRows = computed(() => buildCompraRows(compras.value, insumosLookup.value))

const savingCompra = ref(false)
const savingInsumo = ref(false)
const editingInsumo = ref<InsumoRead | null>(null)

/** T8/FE-DLG-1: the forms live in el-dialog at the usage site. */
const insumoDialogVisible = ref(false)
const comprasDialogVisible = ref(false)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [insumosPage_, comprasPage_, categoriasList, insumosLookup_] = await Promise.all([
      insumosApi.list(
        buildListParams({
          page: insumosPage.value,
          pageSize: insumosPageSize.value,
          filtros: { categoria_id: filterCategoriaId.value },
          q: insumoQ.value,
          sortBy: insumosSortBy.value ?? undefined,
          sortOrder: insumosSortOrder.value ?? undefined,
        }),
      ),
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
      canManage.value ? categoriasInsumosApi.list() : Promise.resolve({ items: [] as CategoriaInsumoRead[], total: 0 }),
      // D3: join fetches keep the full set (no pagination on lookups).
      insumosApi.list({ limit: 1000 }),
    ])
    insumos.value = insumosPage_.items
    insumosTotal.value = insumosPage_.total
    compras.value = comprasPage_.items
    comprasTotal.value = comprasPage_.total
    categorias.value = categoriasList.items
    insumosLookup.value = insumosLookup_.items
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
  insumosPage.value = 1
  load()
}

function onInsumosFilterChange(): void {
  insumosPage.value = 1
  load()
}

function onComprasSearch(): void {
  comprasPage.value = 1
  load()
}

function onComprasFilterChange(): void {
  comprasPage.value = 1
  load()
}

/** Header column filter (InsumosTable) maps into the categoria_id ref. */
function onInsumosTableFilterChange(filters: { categoria_id?: number | null }): void {
  filterCategoriaId.value = filters.categoria_id ?? null
  onInsumosFilterChange()
}

/** Header column filter (ComprasTable) maps into the insumo ref. */
function onComprasTableFilterChange(filters: { insumo_id?: number | null }): void {
  filterInsumoId.value = filters.insumo_id ?? null
  onComprasFilterChange()
}

/** Server-side column sort (insumos): reset to page 1; null clears the sort. */
function onInsumosTableSortChange(sort: { prop: string; order: 'asc' | 'desc' | null }): void {
  insumosSortBy.value = sort.order === null ? null : sort.prop
  insumosSortOrder.value = sort.order
  onInsumosFilterChange()
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
      <Button :loading="loading" data-test="refresh-inventario" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="inventario-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="insumos">Insumos</Tab>
        <Tab value="compras">Compras</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="insumos">
        <div class="insumo-toolbar">
          <el-input
            v-model="insumoQ"
            clearable
            placeholder="Buscar insumo…"
            data-test="insumo-search"
            class="insumo-search"
            @keyup.enter="onInsumosSearch"
            @clear="onInsumosSearch"
          />
          <el-select
            v-model="filterCategoriaId"
            clearable
            filterable
            placeholder="Filtrar por categoría"
            data-test="insumo-categoria-filter"
            @change="onInsumosFilterChange"
          >
            <el-option v-for="c in categorias" :key="c.id" :label="c.nombre" :value="c.id" />
          </el-select>
          <Button v-if="canManage" data-test="nuevo-insumo" @click="openCreateInsumo">
            Nuevo insumo
          </Button>
        </div>

        <InsumosTable
          :rows="insumos"
          :loading="loading"
          :categorias="categorias"
          :can-edit="canManage"
          @edit="onEditInsumo"
          @delete="onDeleteInsumo"
          @filter-change="onInsumosTableFilterChange"
          @sort-change="onInsumosTableSortChange"
        />
        <Paginator
          class="tabla-paginacion"
          :total-records="insumosTotal"
          :rows="insumosPageSize"
          :first="(insumosPage - 1) * insumosPageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="(e: { first: number; rows: number }) => { insumosPage = Math.floor(e.first / e.rows) + 1; load() }"
        />

        <el-dialog
          v-model="insumoDialogVisible"
          :title="editingInsumo === null ? 'Crear insumo' : 'Editar insumo'"
          :close-on-click-modal="false"
          :close-on-press-escape="!savingInsumo"
          :show-close="!savingInsumo"
          width="720px"
          @closed="resetInsumoDialog"
        >
          <InsumoForm
            v-if="insumoDialogVisible"
            :mode="editingInsumo === null ? 'create' : 'edit'"
            :initial="editingInsumo"
            :categorias="categorias"
            :saving="savingInsumo"
            @submit="submitInsumo"
          />
        </el-dialog>
      </TabPanel>

      <TabPanel value="compras">
        <div class="compras-filtro">
          <el-input
            v-model="compraQ"
            clearable
            placeholder="Buscar por insumo…"
            data-test="compra-search"
            class="compra-search"
            @keyup.enter="onComprasSearch"
            @clear="onComprasSearch"
          />
          <el-select
            v-model="filterInsumoId"
            clearable
            filterable
            placeholder="Filtrar por insumo"
            data-test="compra-filter-select"
            @change="onComprasFilterChange"
          >
            <el-option v-for="i in insumosLookup" :key="i.id" :label="i.nombre" :value="i.id" />
          </el-select>
          <Button v-if="canRegister" data-test="nueva-compra" @click="openCreateCompra">
            Nueva compra
          </Button>
        </div>

        <ComprasTable
          :rows="compraRows"
          :loading="loading"
          :insumos="insumosLookup"
          @filter-change="onComprasTableFilterChange"
          @sort-change="onComprasTableSortChange"
        />
        <Paginator
          class="tabla-paginacion"
          :total-records="comprasTotal"
          :rows="comprasPageSize"
          :first="(comprasPage - 1) * comprasPageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="(e: { first: number; rows: number }) => { comprasPage = Math.floor(e.first / e.rows) + 1; load() }"
        />

        <el-dialog
          v-model="comprasDialogVisible"
          title="Nueva compra"
          :close-on-click-modal="false"
          :close-on-press-escape="!savingCompra"
          :show-close="!savingCompra"
          width="720px"
        >
          <ComprasForm
            v-if="comprasDialogVisible"
            :insumos="insumosLookup"
            :saving="savingCompra"
            @submit="onCreateCompra"
          />
        </el-dialog>
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

.compras-filtro .el-select {
  width: 12rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}
</style>
