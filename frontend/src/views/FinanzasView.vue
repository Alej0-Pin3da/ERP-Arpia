<script setup lang="ts">
/**
 * Finanzas view (PR8, spec MOD-3).
 *
 * Three tabs:
 *  - Movimientos: create form + soft-deletable list. POST /finanzas/movimientos
 *    {tipo Gasto|Inversion|Retiro, descripcion, monto, socio_id?} (201); DELETE
 *    /finanzas/movimientos/{id} returns **200 + MovimientoRead** (NOT 204) —
 *    the row is soft-deleted and disappears from the active list.
 *  - Liquidaciones: one-time settlement (POST /finanzas/liquidaciones -> 201
 *    list[MovimientoRead], one Retiro per socio) with a per-socio result
 *    table; a replay of the same liquidacion_id surfaces the server 409.
 *  - Socios: CRUD over /finanzas/socios — the server enforces the sum-to-100
 *    invariant (create requires an exact 100 total; update may rebalance
 *    below but never above; both 422) and blocks deleting a socio with
 *    payouts (409). PATCH carries the percentage only.
 *
 * Writes are gated operador+ (canRegister); consulta sees read-only lists and
 * no Liquidaciones tab.
 */
import { computed, onMounted, ref } from 'vue'

import { finanzasApi } from '@/api/endpoints'
import LiquidacionesForm from '@/components/finanzas/LiquidacionesForm.vue'
import MovimientosForm from '@/components/finanzas/MovimientosForm.vue'
import MovimientosTable from '@/components/finanzas/MovimientosTable.vue'
import SociosForm from '@/components/finanzas/SociosForm.vue'
import SociosTable from '@/components/finanzas/SociosTable.vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Select from 'primevue/select'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import { useAuthStore } from '@/stores/auth'
import { confirmAction } from '@/utils/confirm'
import { formatMoney } from '@/utils/format'
import { buildListParams } from '@/utils/pagination'
import { showToast } from '@/utils/toast'
import {
  buildLiquidacionRows,
  buildMovimientoRows,
  type LiquidacionCreate,
  type LiquidacionRow,
  type MovimientoCreate,
  type MovimientoRow,
  type MovimientoUpdate,
} from '@/utils/finanzas'
import type {
  MovimientoRead,
  SocioConfiguracionCreate,
  SocioConfiguracionRead,
  SocioConfiguracionUpdate,
} from '@/types/api.d'

const auth = useAuthStore()

/** MOD-3: only operador+ writes; consulta sees the lists only. */
const canRegister = computed(() => auth.role === 'admin' || auth.role === 'operador')

const activeTab = ref('movimientos')
const loading = ref(false)
const error = ref<string | null>(null)

// --- movimientos table: server-side pagination + tipo filter ---------------
const movimientos = ref<MovimientoRead[]>([])
const movimientosTotal = ref(0)
const movimientosPage = ref(1)
const movimientosPageSize = 20
const filterTipo = ref<'Gasto' | 'Inversion' | 'Retiro' | null>(null)
const tipoOptions = [
  { label: 'Gasto', value: 'Gasto' },
  { label: 'Inversión', value: 'Inversion' },
  { label: 'Retiro', value: 'Retiro' },
]
const movimientosSortBy = ref<string | null>(null)
const movimientosSortOrder = ref<'asc' | 'desc' | null>(null)

// --- socios table + lookup --------------------------------------------------
const socios = ref<SocioConfiguracionRead[]>([])
const sociosTotal = ref(0)
const sociosPage = ref(1)
const sociosPageSize = 20
const sociosSortBy = ref<string | null>(null)
const sociosSortOrder = ref<'asc' | 'desc' | null>(null)
/** Full partner set for the socio name join + the socio select (design D3). */
const sociosLookup = ref<SocioConfiguracionRead[]>([])

/** Joined rows: socio name (or '—') + newest-first ledger order. */
const movimientoRows = computed(() => buildMovimientoRows(movimientos.value, sociosLookup.value))

const savingMovimiento = ref(false)
const savingLiquidacion = ref(false)
const savingSocio = ref(false)

const liquidacionRows = ref<LiquidacionRow[]>([])
const editingSocio = ref<SocioConfiguracionRead | null>(null)
/** T9: the movimiento being edited (the dialog opens in edit mode while set;
 *  success clears it, an error keeps it open). */
const editingMovimiento = ref<MovimientoRead | null>(null)

/** T8/FE-DLG-1: the movimientos + socios forms live in el-dialog at the usage site. */
const movimientoDialogVisible = ref(false)
const socioDialogVisible = ref(false)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [movs, sociosPage_, sociosLookup_] = await Promise.all([
      finanzasApi.listMovimientos(
        buildListParams({
          page: movimientosPage.value,
          pageSize: movimientosPageSize,
          filtros: { tipo: filterTipo.value },
          sortBy: movimientosSortBy.value ?? undefined,
          sortOrder: movimientosSortOrder.value ?? undefined,
        }),
      ),
      finanzasApi.listSocios(
        buildListParams({
          page: sociosPage.value,
          pageSize: sociosPageSize,
          sortBy: sociosSortBy.value ?? undefined,
          sortOrder: sociosSortOrder.value ?? undefined,
        }),
      ),
      // D3: the socio select + name join need the full set.
      finanzasApi.listSocios({ limit: 1000 }),
    ])
    movimientos.value = movs.items
    movimientosTotal.value = movs.total
    socios.value = sociosPage_.items
    sociosTotal.value = sociosPage_.total
    sociosLookup.value = sociosLookup_.items
  } catch {
    error.value = 'No se pudo cargar la información de finanzas. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** FE-2: the tipo filter resets the movimientos page to 1 and refetches. */
function onMovimientoFilterChange(): void {
  movimientosPage.value = 1
  load()
}

/** Header column filter (MovimientosTable) drives the same ref as the toolbar. */
function onMovimientoTableFilterChange(filters: {
  tipo?: 'Gasto' | 'Inversion' | 'Retiro' | null
}): void {
  filterTipo.value = filters.tipo ?? null
  onMovimientoFilterChange()
}

/** Server-side column sort: reset to page 1; a null order clears the sort. */
function onMovimientoTableSortChange(sort: { prop: string; order: 'asc' | 'desc' | null }): void {
  movimientosSortBy.value = sort.order === null ? null : sort.prop
  movimientosSortOrder.value = sort.order
  onMovimientoFilterChange()
}

/** Server-side column sort for the socios table (no toolbar filters). */
function onSociosTableSortChange(sort: { prop: string; order: 'asc' | 'desc' | null }): void {
  sociosSortBy.value = sort.order === null ? null : sort.prop
  sociosSortOrder.value = sort.order
  sociosPage.value = 1
  load()
}

/** Surface the server validation detail (422/400/409) when present. */
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

/** MOD-3: POST the MovimientoCreate payload, confirm and refresh. */
async function onCreateMovimiento(payload: MovimientoCreate): Promise<void> {
  savingMovimiento.value = true
  try {
    await finanzasApi.createMovimiento(payload)
    showToast('success', 'Movimiento registrado correctamente')
    movimientoDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo registrar el movimiento. Verifica los datos e inténtalo de nuevo.')
  } finally {
    savingMovimiento.value = false
  }
}

/** MOD-3: soft-delete after a confirm dialog; DELETE answers 200, not 204. */
async function onDeleteMovimiento(row: MovimientoRow): Promise<void> {
  const choice = await confirmAction({
    message: `¿Eliminar el movimiento "${row.descripcion}"?`,
    header: 'Confirmar eliminación',
    acceptLabel: 'Eliminar',
    rejectLabel: 'Cancelar',
  })
  if (choice !== 'accept') return // cancelled
  try {
    await finanzasApi.deleteMovimiento({ movimiento_id: row.id })
    showToast('success', 'Movimiento eliminado correctamente')
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo eliminar el movimiento.')
  }
}

/** MOD-3: run the one-time settlement, show the per-socio result, refresh. */
async function onCreateLiquidacion(payload: LiquidacionCreate): Promise<void> {
  savingLiquidacion.value = true
  try {
    const result = await finanzasApi.createLiquidacion(payload)
    liquidacionRows.value = buildLiquidacionRows(result, socios.value)
    showToast('success', 'Liquidación procesada correctamente')
    await load() // the settlement created Retiro rows
  } catch (err) {
    // 409 replay ("...ya fue procesada") surfaces as-is.
    showToast('error', serverDetail(err) ?? 'No se pudo procesar la liquidación.')
  } finally {
    savingLiquidacion.value = false
  }
}

/** T9: the table emits the joined row; resolve the full MovimientoRead from
 *  the current page state to prefill the edit form. */
function onEditMovimiento(row: MovimientoRow): void {
  editingMovimiento.value = movimientos.value.find((m) => m.id === row.id) ?? null
  movimientoDialogVisible.value = true
}

/** FE-DLG-1: the toolbar button opens the dialog in create mode. */
function openCreateMovimiento(): void {
  editingMovimiento.value = null
  movimientoDialogVisible.value = true
}

/** FE-DLG-2/3: closing without saving discards the edit prefill. */
function resetMovimientoDialog(): void {
  editingMovimiento.value = null
}

/** T8: one @submit entry — route create vs edit by the dialog mode. */
function submitMovimiento(payload: MovimientoCreate | MovimientoUpdate): void {
  if (editingMovimiento.value === null) {
    void onCreateMovimiento(payload as MovimientoCreate)
  } else {
    void onUpdateMovimiento(payload as MovimientoUpdate)
  }
}

/** T9: PATCH the movement. Success closes the dialog and refreshes; an
 *  error (e.g. the FIN-2 422 on liquidacion rows) shows the message and keeps
 *  the dialog open. */
async function onUpdateMovimiento(payload: MovimientoUpdate): Promise<void> {
  if (editingMovimiento.value === null) return
  savingMovimiento.value = true
  try {
    await finanzasApi.updateMovimiento({ movimiento_id: editingMovimiento.value.id }, payload)
    showToast('success', 'Movimiento actualizado correctamente')
    movimientoDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo actualizar el movimiento. Verifica los datos e inténtalo de nuevo.')
  } finally {
    savingMovimiento.value = false
  }
}
/** MOD-3: POST a socio; the exact-100 sum rule is enforced server-side (422). */
async function onCreateSocio(payload: SocioConfiguracionCreate): Promise<void> {
  savingSocio.value = true
  try {
    await finanzasApi.createSocio(payload)
    showToast('success', 'Socio creado correctamente')
    socioDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo crear el socio.')
  } finally {
    savingSocio.value = false
  }
}

function onEditSocio(row: SocioConfiguracionRead): void {
  editingSocio.value = row
  socioDialogVisible.value = true
}

/** FE-DLG-1: the toolbar button opens the dialog in create mode. */
function openCreateSocio(): void {
  editingSocio.value = null
  socioDialogVisible.value = true
}

/** FE-DLG-2/3: closing without saving discards the edit prefill. */
function resetSocioDialog(): void {
  editingSocio.value = null
}

/** T8: one @submit entry — route create vs edit by the dialog mode. */
function submitSocio(payload: SocioConfiguracionCreate | SocioConfiguracionUpdate): void {
  if (editingSocio.value === null) {
    void onCreateSocio(payload as SocioConfiguracionCreate)
  } else {
    void onUpdateSocio(payload as SocioConfiguracionUpdate)
  }
}

/** MOD-3: PATCH the percentage (name is not updatable server-side). */
async function onUpdateSocio(payload: SocioConfiguracionUpdate): Promise<void> {
  if (editingSocio.value === null) return
  savingSocio.value = true
  try {
    await finanzasApi.updateSocio({ socio_id: editingSocio.value.id }, payload)
    showToast('success', 'Socio actualizado correctamente')
    socioDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo actualizar el socio.')
  } finally {
    savingSocio.value = false
  }
}

/** MOD-3: delete a socio after a confirm dialog; 409 (payouts) surfaced. */
async function onDeleteSocio(row: SocioConfiguracionRead): Promise<void> {
  const choice = await confirmAction({
    message: `¿Eliminar el socio "${row.nombre}"?`,
    header: 'Confirmar eliminación',
    acceptLabel: 'Eliminar',
    rejectLabel: 'Cancelar',
  })
  if (choice !== 'accept') return // cancelled
  try {
    await finanzasApi.deleteSocio({ socio_id: row.id })
    showToast('success', 'Socio eliminado correctamente')
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo eliminar el socio.')
  }
}

onMounted(load)
</script>

<template>
  <section class="finanzas">
    <header class="finanzas-header">
      <h2>Finanzas</h2>
      <Button :loading="loading" data-test="refresh-finanzas" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="finanzas-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="movimientos">Movimientos</Tab>
        <Tab v-if="canRegister" value="liquidaciones">Liquidaciones</Tab>
        <Tab value="socios">Socios</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="movimientos">
        <div class="finanzas-toolbar">
          <Select
            v-model="filterTipo"
            :options="tipoOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Filtrar por tipo"
            :show-clear="true"
            data-test="movimiento-tipo-filter"
            class="movimiento-tipo-filter"
            @change="onMovimientoFilterChange"
          />
          <Button v-if="canRegister" data-test="nuevo-movimiento" @click="openCreateMovimiento">
            Nuevo movimiento
          </Button>
        </div>
        <MovimientosTable
          :rows="movimientoRows"
          :loading="loading"
          :can-delete="canRegister"
          :can-edit="canRegister"
          @delete="onDeleteMovimiento"
          @edit="onEditMovimiento"
          @filter-change="onMovimientoTableFilterChange"
          @sort-change="onMovimientoTableSortChange"
        />
        <Paginator
          class="tabla-paginacion"
          :total-records="movimientosTotal"
          :rows="movimientosPageSize"
          :first="(movimientosPage - 1) * movimientosPageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="(e: { first: number; rows: number }) => { movimientosPage = Math.floor(e.first / e.rows) + 1; load() }"
        />

        <Dialog
          v-model:visible="movimientoDialogVisible"
          :header="editingMovimiento === null ? 'Registrar movimiento' : 'Editar movimiento'"
          modal
          position="top"
          style="width: 720px"
          :dismissable-mask="false"
          :close-on-escape="!savingMovimiento"
          :closable="!savingMovimiento"
          @after-hide="resetMovimientoDialog"
        >
          <MovimientosForm
            v-if="movimientoDialogVisible"
            :mode="editingMovimiento === null ? 'create' : 'edit'"
            :initial="editingMovimiento"
            :socios="sociosLookup"
            :saving="savingMovimiento"
            @submit="submitMovimiento"
          />
        </Dialog>
      </TabPanel>

      <TabPanel v-if="canRegister" value="liquidaciones">
        <LiquidacionesForm :saving="savingLiquidacion" @submit="onCreateLiquidacion" />

        <div v-if="liquidacionRows.length > 0" class="liquidacion-result" data-test="liquidacion-result">
          <h3>Resultado de la liquidación</h3>
          <DataTable :value="liquidacionRows">
            <Column field="socio" header="Socio" style="min-width: 220px" />
            <Column header="Monto" style="width: 180px" align="right">
              <template #body="{ data }">{{ formatMoney(data.monto) }}</template>
            </Column>
          </DataTable>
        </div>
      </TabPanel>

      <TabPanel value="socios">
        <div class="socios-toolbar">
          <Button v-if="canRegister" data-test="nuevo-socio" @click="openCreateSocio">
            Nuevo socio
          </Button>
        </div>
        <SociosTable
          :rows="socios"
          :loading="loading"
          :can-edit="canRegister"
          @edit="onEditSocio"
          @delete="onDeleteSocio"
          @sort-change="onSociosTableSortChange"
        />
        <Paginator
          class="tabla-paginacion"
          :total-records="sociosTotal"
          :rows="sociosPageSize"
          :first="(sociosPage - 1) * sociosPageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="(e: { first: number; rows: number }) => { sociosPage = Math.floor(e.first / e.rows) + 1; load() }"
        />

        <Dialog
          v-model:visible="socioDialogVisible"
          :header="editingSocio === null ? 'Crear socio' : 'Editar socio'"
          modal
          position="top"
          style="width: 560px"
          :dismissable-mask="false"
          :close-on-escape="!savingSocio"
          :closable="!savingSocio"
          @after-hide="resetSocioDialog"
        >
          <SociosForm
            v-if="socioDialogVisible"
            :mode="editingSocio === null ? 'create' : 'edit'"
            :initial="editingSocio"
            :saving="savingSocio"
            @submit="submitSocio"
          />
        </Dialog>
      </TabPanel>
      </TabPanels>
    </Tabs>
  </section>
</template>

<style scoped>
.finanzas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.finanzas-header h2 {
  margin: 0;
}

.finanzas-error {
  margin-bottom: 1rem;
}

.finanzas-toolbar {
  display: flex;
  gap: 0.75rem;
  max-width: 42rem;
  margin-bottom: 1rem;
}

.movimiento-tipo-filter {
  width: 12rem;
}

.socios-toolbar {
  margin-bottom: 1rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}

.liquidacion-result {
  margin-top: 1.5rem;
  max-width: 40rem;
}

.liquidacion-result h3 {
  margin: 0 0 0.5rem;
}
</style>
