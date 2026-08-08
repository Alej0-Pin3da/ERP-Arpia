<script setup lang="ts">
/**
 * Inventario view (PR9, spec MOD-4).
 *
 * Two tabs:
 *  - Insumos: the master list from GET /insumos — `nombre_categoria` is
 *    JOINED SERVER-SIDE (no client join), quantities/costs render es-CO and
 *    rows below their minimum are highlighted (stockSeverity, dashboard
 *    pattern). The create/edit form + Editar/Eliminar actions are ADMIN ONLY
 *    (backend require_admin); operador/consulta never see them.
 *  - Compras: GET /compras-insumos with an optional insumo_id filter, the
 *    register form (operador+) and the list. POST /compras-insumos runs the
 *    WAC service server-side (updates stock_actual and costo_promedio_actual),
 *    so a successful compra refreshes BOTH tabs — the insumos list shows the
 *    stock/cost change immediately.
 *
 * Writes: compras operador+ (canRegister); insumo master admin only
 * (canManage). Consulta is read-only everywhere.
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { categoriasInsumosApi, comprasApi, insumosApi } from '@/api/endpoints'
import ComprasForm from '@/components/inventario/ComprasForm.vue'
import ComprasTable from '@/components/inventario/ComprasTable.vue'
import InsumoForm from '@/components/inventario/InsumoForm.vue'
import InsumosTable from '@/components/inventario/InsumosTable.vue'
import { useAuthStore } from '@/stores/auth'
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

const insumos = ref<InsumoRead[]>([])
const compras = ref<CompraInsumoRead[]>([])
const categorias = ref<CategoriaInsumoRead[]>([])

/** Optional GET /compras-insumos?insumo_id filter (clearable select). */
const filterInsumoId = ref<number | null>(null)

/** Joined compra rows: insumo name + client-computed costo_total, newest first. */
const compraRows = computed(() => buildCompraRows(compras.value, insumos.value))

const savingCompra = ref(false)
const savingInsumo = ref(false)
const editingInsumo = ref<InsumoRead | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [insumosList, comprasList, categoriasList] = await Promise.all([
      insumosApi.list({ limit: 1000 }), // backend GET /insumos defaults to limit=50
      comprasApi.list(buildComprasListParams({ insumo_id: filterInsumoId.value })),
      // Categoria options only feed the admin-only form — skip for other roles.
      canManage.value ? categoriasInsumosApi.list() : Promise.resolve([]),
    ])
    insumos.value = insumosList
    compras.value = comprasList
    categorias.value = categoriasList
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
      </el-tab-pane>

      <el-tab-pane label="Compras" name="compras">
        <div class="compras-filtro">
          <el-select
            v-model="filterInsumoId"
            clearable
            filterable
            placeholder="Filtrar por insumo"
            data-test="compra-filter-select"
            @change="load"
          >
            <el-option v-for="i in insumos" :key="i.id" :label="i.nombre" :value="i.id" />
          </el-select>
        </div>

        <ComprasForm
          v-if="canRegister"
          :insumos="insumos"
          :saving="savingCompra"
          class="compra-form-section"
          @submit="onCreateCompra"
        />
        <ComprasTable :rows="compraRows" :loading="loading" />
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

.compras-filtro {
  max-width: 20rem;
  margin-bottom: 1rem;
}

.compras-filtro .el-select {
  width: 100%;
}

.compra-form-section {
  margin-bottom: 1rem;
}
</style>
