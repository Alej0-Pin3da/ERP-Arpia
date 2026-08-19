<script setup lang="ts">
/**
 * Devoluciones view (task 2.3, spec MOD-2 + ui-mantenimiento PR1 T7).
 *
 * Two sections: the returns list and the create form.
 *  - List: server-side paginated GET /devoluciones ({items,total} + PrimeVue
 *    Paginator) with optional filters (venta_id, fecha range) — items are
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
import Button from 'primevue/button'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
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

/** T8/FE-DLG-1: the register form lives in an el-dialog opened from the toolbar. */
const devolucionDialogVisible = ref(false)

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

/** FE-DLG-1: the toolbar button opens the register dialog in create mode. */
function openCreateDevolucion(): void {
  devolucionDialogVisible.value = true
}

/** MOD-2: POST the DevolucionCreate payload, confirm and refresh the list. */
async function onSubmit(payload: DevolucionCreate): Promise<void> {
  saving.value = true
  try {
    await devolucionesApi.create(payload)
    ElMessage.success('Devolución registrada correctamente')
    devolucionDialogVisible.value = false // FE-DLG-2: success closes the dialog
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
      <Button :loading="loading" data-test="refresh-devoluciones" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="devoluciones-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

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
      <Button text data-test="apply-filters" @click="applyFilters">Filtrar</Button>
      <Button severity="secondary" data-test="clear-filters" @click="clearFilters">Limpiar</Button>
      <Button v-if="canRegister" data-test="nueva-devolucion" @click="openCreateDevolucion">
        Nueva devolución
      </Button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Listado" name="listado">
        <DevolucionesTable :rows="rows" :loading="loading" />
        <Paginator
          class="tabla-paginacion"
          :total-records="total"
          :rows="pageSize"
          :first="(page - 1) * pageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="(e: { first: number; rows: number }) => { page = Math.floor(e.first / e.rows) + 1; load() }"
        />
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="devolucionDialogVisible"
      title="Nueva devolución"
      :close-on-click-modal="false"
      :close-on-press-escape="!saving"
      :show-close="!saving"
      width="640px"
    >
      <DevolucionesForm
        v-if="devolucionDialogVisible"
        :productos="productos"
        :load-variantes="loadVariantes"
        :saving="saving"
        @submit="onSubmit"
      />
    </el-dialog>
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
