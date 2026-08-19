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

import { devolucionesApi, productosApi } from '@/api/endpoints'
import DevolucionesForm from '@/components/devoluciones/DevolucionesForm.vue'
import DevolucionesTable from '@/components/devoluciones/DevolucionesTable.vue'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import { useAuthStore } from '@/stores/auth'
import { buildListParams } from '@/utils/pagination'
import { showToast } from '@/utils/toast'
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

/** T8/FE-DLG-1: the register form lives in a PrimeVue Dialog opened from the toolbar. */
const devolucionDialogVisible = ref(false)

/** List filters (MOD-2: venta_id, fecha_desde, fecha_hasta). */
const filtros = reactive({ venta_id: null as number | null, fecha_desde: '', fecha_hasta: '' })

/**
 * DatePicker works with Date objects (MIG-2); the API contract wants
 * 'YYYY-MM-DD' strings — the computed proxies convert at the boundary and
 * keep `filtros` unchanged for buildListParams and clearFilters.
 */
function fechaToDate(s: string): Date | null {
  if (s === '') return null
  const [y, m, d] = s.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function fechaToString(d: Date | null): string {
  if (d === null) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const fechaDesdeModel = computed({
  get: () => fechaToDate(filtros.fecha_desde),
  set: (v: Date | null) => {
    filtros.fecha_desde = fechaToString(v)
  },
})

const fechaHastaModel = computed({
  get: () => fechaToDate(filtros.fecha_hasta),
  set: (v: Date | null) => {
    filtros.fecha_hasta = fechaToString(v)
  },
})

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

/** Paginator @page: recompute the 1-based page from the 0-based first index. */
function onPage(e: { first: number; rows: number }): void {
  page.value = Math.floor(e.first / e.rows) + 1
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
    showToast('success', 'Devolución registrada correctamente')
    devolucionDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? 'No se pudo registrar la devolución. Verifica los datos e inténtalo de nuevo.')
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
      <InputNumber
        v-model="filtros.venta_id"
        :min="1"
        :step="1"
        :show-buttons="false"
        placeholder="Venta"
        class="filter-field"
        data-test="filtro-venta"
      />
      <DatePicker
        v-model="fechaDesdeModel"
        dateFormat="yy-mm-dd"
        placeholder="Desde"
        class="filter-field"
        data-test="filtro-desde"
      />
      <DatePicker
        v-model="fechaHastaModel"
        dateFormat="yy-mm-dd"
        placeholder="Hasta"
        class="filter-field"
        data-test="filtro-hasta"
      />
      <Button text data-test="apply-filters" @click="applyFilters">Filtrar</Button>
      <Button severity="secondary" data-test="clear-filters" @click="clearFilters">Limpiar</Button>
      <Button v-if="canRegister" data-test="nueva-devolucion" @click="openCreateDevolucion">
        Nueva devolución
      </Button>
    </div>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="listado">Listado</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="listado">
        <DevolucionesTable :rows="rows" :loading="loading" />
        <Paginator
          class="tabla-paginacion"
          :total-records="total"
          :rows="pageSize"
          :first="(page - 1) * pageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="onPage"
        />
      </TabPanel>
      </TabPanels>
    </Tabs>

    <Dialog
      v-model:visible="devolucionDialogVisible"
      header="Nueva devolución"
      modal
      position="top"
      style="width: 640px"
      :dismissable-mask="false"
      :close-on-escape="!saving"
      :closable="!saving"
    >
      <DevolucionesForm
        v-if="devolucionDialogVisible"
        :productos="productos"
        :load-variantes="loadVariantes"
        :saving="saving"
        @submit="onSubmit"
      />
    </Dialog>
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
