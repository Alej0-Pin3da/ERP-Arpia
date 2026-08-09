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
 *    proveedor_id + insumo_id filters. POST runs the WAC service server-side
 *    (updates stock/cost), so a successful compra refreshes BOTH tabs.
 *
 * Lookup joins (ComprasForm options, filter select, compra name join) fetch
 * the full insumos set with limit:1000 against `.items` (design D3) — table
 * views use real pagination, join fetches keep the lookup hack.
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { categoriasInsumosApi, comprasApi, insumosApi } from '@/api/endpoints'
import ComprasForm from '@/components/inventario/ComprasForm.vue'
import ComprasTable from '@/components/inventario/ComprasTable.vue'
import InsumoForm from '@/components/inventario/InsumoForm.vue'
import InsumosTable from '@/components/inventario/InsumosTable.vue'
import { useAuthStore } from '@/stores/auth'
import { buildListParams } from '@/utils/pagination'
import {
  buildCompraRows,
  buildComprasListParams,
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

// --- compras table: server-side pagination + filters -----------------------
const compras = ref<CompraInsumoRead[]>([])
const comprasTotal = ref(0)
const comprasPage = ref(1)
const comprasPageSize = ref(20)
const compraQ = ref('')
/** Optional GET /compras-insumos?insumo_id filter (clearable select). */
const filterInsumoId = ref<number | null>(null)
const filterProveedorId = ref<number | null>(null)

// --- lookups (full sets, limit:1000 — design D3) ---------------------------
const insumosLookup = ref<InsumoRead[]>([])
const categorias = ref<CategoriaInsumoRead[]>([])

/** Joined compra rows: insumo name + client-computed costo_total, newest first. */
const compraRows = computed(() => buildCompraRows(compras.value, insumosLookup.value))

const savingCompra = ref(false)
const savingInsumo = ref(false)
const editingInsumo = ref<InsumoRead | null>(null)

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
        }),
      ),
      comprasApi.list(
        buildListParams({
          page: comprasPage.value,
          pageSize: comprasPageSize.value,
          filtros: { insumo_id: filterInsumoId.value, proveedor_id: filterProveedorId.value },
          q: compraQ.value,
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

/** MOD-4: POST the compra — the WAC service updates stock/cost server-side,
 *  so the refresh reloads BOTH the compras list and the insumos list. */
async function onCreateCompra(payload: CompraInsumoCreate): Promise<void> {
  savingCompra.value = true
  try {
    await comprasApi.create(payload)
    ElMessage.success('Compra registrada correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo registrar la compra. Verifica los datos e inténtalo de nuevo.')
  } finally {
    savingCompra.value = false
  }
}

/** MOD-4: admin — POST the insumo master row. */
async function onCreateInsumo(payload: InsumoCreate): Promise<void> {
  savingInsumo.value = true
  try {
    await insumosApi.create(payload)
    ElMessage.success('Insumo creado correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo crear el insumo.')
  } finally {
    savingInsumo.value = false
  }
}

function onEditInsumo(row: InsumoRead): void {
  editingInsumo.value = row
}

function cancelEditInsumo(): void {
  editingInsumo.value = null
}

/** MOD-4: admin — PUT the insumo master row, then back to the create form. */
async function onUpdateInsumo(payload: InsumoUpdate): Promise<void> {
  if (editingInsumo.value === null) return
  savingInsumo.value = true
  try {
    await insumosApi.update({ insumo_id: editingInsumo.value.id }, payload)
    ElMessage.success('Insumo actualizado correctamente')
    editingInsumo.value = null
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo actualizar el insumo.')
  } finally {
    savingInsumo.value = false
  }
}

/** MOD-4: admin — delete after a confirm dialog; DELETE answers 204. */
async function onDeleteInsumo(row: InsumoRead): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `¿Eliminar el insumo "${row.nombre}"?`,
      'Confirmar eliminación',
      { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
    )
  } catch {
    return // cancelled
  }
  try {
    await insumosApi.delete({ insumo_id: row.id })
    ElMessage.success('Insumo eliminado correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar el insumo.')
  }
}

onMounted(load)
</script>

<template>
  <section class="inventario">
    <header class="inventario-header">
      <h2>Inventario</h2>
      <el-button :loading="loading" data-test="refresh-inventario" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="inventario-error"
    />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Insumos" name="insumos">
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
        </div>

        <div v-if="canManage" class="insumo-form-section">
          <template v-if="editingInsumo === null">
            <h3>Crear insumo</h3>
            <InsumoForm mode="create" :categorias="categorias" :saving="savingInsumo" @submit="onCreateInsumo" />
          </template>
          <template v-else>
            <h3>Editar insumo</h3>
            <InsumoForm
              mode="edit"
              :initial="editingInsumo"
              :categorias="categorias"
              :saving="savingInsumo"
              @submit="onUpdateInsumo"
            />
            <el-button size="small" data-test="cancel-edit-insumo" @click="cancelEditInsumo">
              Cancelar edición
            </el-button>
          </template>
        </div>

        <InsumosTable :rows="insumos" :loading="loading" :can-edit="canManage" @edit="onEditInsumo" @delete="onDeleteInsumo" />
        <el-pagination
          class="tabla-paginacion"
          background
          layout="total, prev, pager, next"
          :total="insumosTotal"
          :page-size="insumosPageSize"
          :current-page="insumosPage"
          @current-change="(p: number) => { insumosPage = p; load() }"
        />
      </el-tab-pane>

      <el-tab-pane label="Compras" name="compras">
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
          <el-select
            v-model="filterProveedorId"
            clearable
            filterable
            placeholder="Filtrar por proveedor"
            data-test="compra-proveedor-filter"
            @change="onComprasFilterChange"
          />
        </div>

        <ComprasForm
          v-if="canRegister"
          :insumos="insumosLookup"
          :saving="savingCompra"
          class="compra-form-section"
          @submit="onCreateCompra"
        />
        <ComprasTable :rows="compraRows" :loading="loading" />
        <el-pagination
          class="tabla-paginacion"
          background
          layout="total, prev, pager, next"
          :total="comprasTotal"
          :page-size="comprasPageSize"
          :current-page="comprasPage"
          @current-change="(p: number) => { comprasPage = p; load() }"
        />
      </el-tab-pane>
    </el-tabs>
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

.insumo-form-section {
  margin-bottom: 1rem;
  max-width: 56rem;
}

.insumo-form-section h3 {
  margin: 0 0 0.5rem;
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

.compra-form-section {
  margin-bottom: 1rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}
</style>
