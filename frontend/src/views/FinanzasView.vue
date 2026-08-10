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
import { ElMessage, ElMessageBox } from 'element-plus'

import { finanzasApi } from '@/api/endpoints'
import LiquidacionesForm from '@/components/finanzas/LiquidacionesForm.vue'
import MovimientosForm from '@/components/finanzas/MovimientosForm.vue'
import MovimientosTable from '@/components/finanzas/MovimientosTable.vue'
import SociosForm from '@/components/finanzas/SociosForm.vue'
import SociosTable from '@/components/finanzas/SociosTable.vue'
import { useAuthStore } from '@/stores/auth'
import { formatMoney } from '@/utils/format'
import { buildListParams } from '@/utils/pagination'
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
    ElMessage.success('Movimiento registrado correctamente')
    movimientoDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo registrar el movimiento. Verifica los datos e inténtalo de nuevo.')
  } finally {
    savingMovimiento.value = false
  }
}

/** MOD-3: soft-delete after a confirm dialog; DELETE answers 200, not 204. */
async function onDeleteMovimiento(row: MovimientoRow): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `¿Eliminar el movimiento "${row.descripcion}"?`,
      'Confirmar eliminación',
      { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
    )
  } catch {
    return // cancelled
  }
  try {
    await finanzasApi.deleteMovimiento({ movimiento_id: row.id })
    ElMessage.success('Movimiento eliminado correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar el movimiento.')
  }
}

/** MOD-3: run the one-time settlement, show the per-socio result, refresh. */
async function onCreateLiquidacion(payload: LiquidacionCreate): Promise<void> {
  savingLiquidacion.value = true
  try {
    const result = await finanzasApi.createLiquidacion(payload)
    liquidacionRows.value = buildLiquidacionRows(result, socios.value)
    ElMessage.success('Liquidación procesada correctamente')
    await load() // the settlement created Retiro rows
  } catch (err) {
    // 409 replay ("...ya fue procesada") surfaces as-is.
    ElMessage.error(serverDetail(err) ?? 'No se pudo procesar la liquidación.')
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
    ElMessage.success('Movimiento actualizado correctamente')
    movimientoDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo actualizar el movimiento. Verifica los datos e inténtalo de nuevo.')
  } finally {
    savingMovimiento.value = false
  }
}
/** MOD-3: POST a socio; the exact-100 sum rule is enforced server-side (422). */
async function onCreateSocio(payload: SocioConfiguracionCreate): Promise<void> {
  savingSocio.value = true
  try {
    await finanzasApi.createSocio(payload)
    ElMessage.success('Socio creado correctamente')
    socioDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo crear el socio.')
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
    ElMessage.success('Socio actualizado correctamente')
    socioDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo actualizar el socio.')
  } finally {
    savingSocio.value = false
  }
}

/** MOD-3: delete a socio after a confirm dialog; 409 (payouts) surfaced. */
async function onDeleteSocio(row: SocioConfiguracionRead): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `¿Eliminar el socio "${row.nombre}"?`,
      'Confirmar eliminación',
      { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
    )
  } catch {
    return // cancelled
  }
  try {
    await finanzasApi.deleteSocio({ socio_id: row.id })
    ElMessage.success('Socio eliminado correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar el socio.')
  }
}

onMounted(load)
</script>

<template>
  <section class="finanzas">
    <header class="finanzas-header">
      <h2>Finanzas</h2>
      <el-button :loading="loading" data-test="refresh-finanzas" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="finanzas-error"
    />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Movimientos" name="movimientos">
        <div class="finanzas-toolbar">
          <el-select
            v-model="filterTipo"
            clearable
            placeholder="Filtrar por tipo"
            data-test="movimiento-tipo-filter"
            @change="onMovimientoFilterChange"
          >
            <el-option label="Gasto" value="Gasto" />
            <el-option label="Inversión" value="Inversion" />
            <el-option label="Retiro" value="Retiro" />
          </el-select>
          <el-button v-if="canRegister" type="primary" data-test="nuevo-movimiento" @click="openCreateMovimiento">
            Nuevo movimiento
          </el-button>
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
        <el-pagination
          class="tabla-paginacion"
          background
          layout="total, prev, pager, next"
          :total="movimientosTotal"
          :page-size="movimientosPageSize"
          :current-page="movimientosPage"
          @current-change="(p: number) => { movimientosPage = p; load() }"
        />

        <el-dialog
          v-model="movimientoDialogVisible"
          :title="editingMovimiento === null ? 'Registrar movimiento' : 'Editar movimiento'"
          :close-on-click-modal="false"
          :close-on-press-escape="!savingMovimiento"
          :show-close="!savingMovimiento"
          width="720px"
          @closed="resetMovimientoDialog"
        >
          <MovimientosForm
            v-if="movimientoDialogVisible"
            :mode="editingMovimiento === null ? 'create' : 'edit'"
            :initial="editingMovimiento"
            :socios="sociosLookup"
            :saving="savingMovimiento"
            @submit="submitMovimiento"
          />
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane v-if="canRegister" label="Liquidaciones" name="liquidaciones">
        <LiquidacionesForm :saving="savingLiquidacion" @submit="onCreateLiquidacion" />

        <div v-if="liquidacionRows.length > 0" class="liquidacion-result" data-test="liquidacion-result">
          <h3>Resultado de la liquidación</h3>
          <el-table :data="liquidacionRows">
            <el-table-column prop="socio" label="Socio" min-width="220" />
            <el-table-column label="Monto" width="180" align="right">
              <template #default="{ row }">{{ formatMoney(row.monto) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Socios" name="socios">
        <div class="socios-toolbar">
          <el-button v-if="canRegister" type="primary" data-test="nuevo-socio" @click="openCreateSocio">
            Nuevo socio
          </el-button>
        </div>
        <SociosTable
          :rows="socios"
          :loading="loading"
          :can-edit="canRegister"
          @edit="onEditSocio"
          @delete="onDeleteSocio"
          @sort-change="onSociosTableSortChange"
        />
        <el-pagination
          class="tabla-paginacion"
          background
          layout="total, prev, pager, next"
          :total="sociosTotal"
          :page-size="sociosPageSize"
          :current-page="sociosPage"
          @current-change="(p: number) => { sociosPage = p; load() }"
        />

        <el-dialog
          v-model="socioDialogVisible"
          :title="editingSocio === null ? 'Crear socio' : 'Editar socio'"
          :close-on-click-modal="false"
          :close-on-press-escape="!savingSocio"
          :show-close="!savingSocio"
          width="560px"
          @closed="resetSocioDialog"
        >
          <SociosForm
            v-if="socioDialogVisible"
            :mode="editingSocio === null ? 'create' : 'edit'"
            :initial="editingSocio"
            :saving="savingSocio"
            @submit="submitSocio"
          />
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
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

.finanzas-toolbar .el-select {
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
