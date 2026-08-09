<script setup lang="ts">
/**
 * Devoluciones view (task 2.3, spec MOD-2 + ui-mantenimiento PR1 T7).
 *
 * Two sections: the returns list and the create form.
 *  - List: server-side paginated GET /devoluciones ({items,total} +
 *    el-pagination) with optional filters (venta_id, fecha range) — items are
 *    joined client-side with /productos?limit=1000 (`Producto #{id}` fallback,
 *    `.items` per D3).
 *  - Create: DevolucionesForm emits the DevolucionCreate payload; the view
 *    owns the POST, the success message and the list refresh. Form hidden for
 *    consulta (read-only role).
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { devolucionesApi, productosApi } from '@/api/endpoints'
import DevolucionesForm from '@/components/devoluciones/DevolucionesForm.vue'
import DevolucionesTable from '@/components/devoluciones/DevolucionesTable.vue'
import { useAuthStore } from '@/stores/auth'
import { buildListParams } from '@/utils/pagination'
import { buildDevolucionRows, type DevolucionCreate, type DevolucionRow } from '@/utils/devoluciones'
import type { ProductoRead, VarianteProductoRead } from '@/types/api.d'

const auth = useAuthStore()

/** MOD-2: only operador+ registers; consulta sees the list only. */
const canRegister = computed(() => auth.role === 'admin' || auth.role === 'operador')

const activeTab = ref('listado')
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const rows = ref<DevolucionRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const productos = ref<ProductoRead[]>([])

/** List filters (MOD-2: venta_id, fecha_desde, fecha_hasta). */
const filtros = reactive({ venta_id: null as number | null, fecha_desde: '', fecha_hasta: '' })

/** Variante fetcher handed to the form (productosApi.listVariantes). */
async function loadVariantes(productoId: number): Promise<VarianteProductoRead[]> {
  return productosApi.listVariantes({ producto_id: productoId })
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [devolucionesPage, productosList] = await Promise.all([
      devolucionesApi.list(
        buildListParams({
          page: page.value,
          pageSize,
          filtros: {
            venta_id: filtros.venta_id,
            fecha_desde: filtros.fecha_desde === '' ? null : filtros.fecha_desde,
            fecha_hasta: filtros.fecha_hasta === '' ? null : filtros.fecha_hasta,
          },
        }),
      ),
      productosApi.list({ limit: 1000 }), // D3: lookup join keeps the full set
    ])
    productos.value = productosList.items
    total.value = devolucionesPage.total
    rows.value = buildDevolucionRows(devolucionesPage.items, productos.value)
  } catch {
    error.value = 'No se pudo cargar la lista de devoluciones. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** FE-2: filter changes reset to page 1 and refetch. */
function applyFilters(): void {
  page.value = 1
  void load()
}

function clearFilters(): void {
  filtros.venta_id = null
  filtros.fecha_desde = ''
  filtros.fecha_hasta = ''
  page.value = 1
  void load()
}

/** Surface the server validation detail (422 etc.) when present. */
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

/** MOD-2: POST the DevolucionCreate payload, confirm and refresh the list. */
async function onSubmit(payload: DevolucionCreate): Promise<void> {
  saving.value = true
  try {
    await devolucionesApi.create(payload)
    ElMessage.success('Devolución registrada correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo registrar la devolución. Verifica los datos e inténtalo de nuevo.')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="devoluciones">
    <header class="devoluciones-header">
      <h2>Devoluciones</h2>
      <el-button :loading="loading" data-test="refresh-devoluciones" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="devoluciones-error"
    />

    <div class="filters" data-test="filters">
      <el-input-number
        v-model="filtros.venta_id"
        :min="1"
        :step="1"
        :controls="false"
        placeholder="Venta"
        class="filter-field"
        data-test="filtro-venta"
      />
      <el-date-picker
        v-model="filtros.fecha_desde"
        type="date"
        placeholder="Desde"
        value-format="YYYY-MM-DD"
        class="filter-field"
        data-test="filtro-desde"
      />
      <el-date-picker
        v-model="filtros.fecha_hasta"
        type="date"
        placeholder="Hasta"
        value-format="YYYY-MM-DD"
        class="filter-field"
        data-test="filtro-hasta"
      />
      <el-button type="primary" plain data-test="apply-filters" @click="applyFilters">Filtrar</el-button>
      <el-button data-test="clear-filters" @click="clearFilters">Limpiar</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Listado" name="listado">
        <DevolucionesTable :rows="rows" :loading="loading" />
        <el-pagination
          class="tabla-paginacion"
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="(p: number) => { page = p; load() }"
        />
      </el-tab-pane>

      <el-tab-pane v-if="canRegister" label="Registrar devolución" name="registrar">
        <DevolucionesForm
          :productos="productos"
          :load-variantes="loadVariantes"
          :saving="saving"
          @submit="onSubmit"
        />
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<style scoped>
.devoluciones-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.devoluciones-header h2 {
  margin: 0;
}

.devoluciones-error {
  margin-bottom: 1rem;
}

.filters {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filter-field {
  width: 10rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}
</style>
