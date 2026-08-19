<script setup lang="ts">
/**
 * Ventas view (tasks 2.1+2.2, spec MOD-1 + ui-mantenimiento PR1 T7).
 *
 * Two tabs: the sales list and the register form.
 *  - List: server-side paginated GET /ventas ({items,total} + canal_venta /
 *    estado filters, design D3), joined client-side with /productos
 *    (limit 1000, `.items`), their variantes (fetched ONLY for products
 *    present in the current page) and /clientes names (limit 1000).
 *  - Register: VentasForm emits the VentaCreate payload; the view owns the
 *    POST, the success message and the list refresh. The form is hidden for
 *    consulta (read-only role — MOD-1 "consulta sees a read-only list").
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'

import { clientesApi, productosApi, ventasApi } from '@/api/endpoints'
import VentasForm from '@/components/ventas/VentasForm.vue'
import VentasTable from '@/components/ventas/VentasTable.vue'
import { useAuthStore } from '@/stores/auth'
import { buildListParams } from '@/utils/pagination'
import {
  buildVentaRows,
  type VentaCreate,
  type VentaRow,
} from '@/utils/ventas'
import type {
  ClienteRead,
  ProductoRead,
  VarianteProductoRead,
  VentaRead,
} from '@/types/api.d'

const auth = useAuthStore()

/** MOD-1: only operador+ registers; consulta sees the list only. */
const canRegister = computed(() => auth.role === 'admin' || auth.role === 'operador')

const activeTab = ref('listado')
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const rows = ref<VentaRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filterCanal = ref<'web' | 'whatsapp' | 'instagram' | 'feria' | null>(null)
const filterEstado = ref<'completada' | 'anulada' | null>(null)
const filterProductoId = ref<number | null>(null)
const sortBy = ref<string | null>(null)
const sortOrder = ref<'asc' | 'desc' | null>(null)
const productos = ref<ProductoRead[]>([])
const clientes = ref<ClienteRead[]>([])

/** T8/FE-DLG-1: the register form lives in an el-dialog opened from the toolbar. */
const ventaDialogVisible = ref(false)
/** The venta being edited; null = create mode (the dialog routes PUT vs POST). */
const editingVenta = ref<VentaRead | null>(null)
/** Raw page items (VentaRead) so edit resolves the full record from the row. */
const rawVentas = ref<VentaRead[]>([])

/** Variante fetcher handed to the form (productosApi.listVariantes). */
async function loadVariantes(productoId: number): Promise<VarianteProductoRead[]> {
  return productosApi.listVariantes({ producto_id: productoId })
}

/** Variantes for the list join — only for products that have detail rows. */
async function fetchVariantesForVentas(ventas: VentaRow[]): Promise<VarianteProductoRead[]> {
  const ids = [...new Set(ventas.flatMap((v) => v.detalles.map((d) => d.producto_id)))]
  if (ids.length === 0) return []
  const lists = await Promise.all(ids.map((producto_id) => productosApi.listVariantes({ producto_id })))
  return lists.flat()
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [ventasPage, productosList, clientesList] = await Promise.all([
      ventasApi.list(
        buildListParams({
          page: page.value,
          pageSize,
          filtros: {
            canal_venta: filterCanal.value,
            estado: filterEstado.value,
            producto_id: filterProductoId.value,
          },
          sortBy: sortBy.value ?? undefined,
          sortOrder: sortOrder.value ?? undefined,
        }),
      ),
      productosApi.list({ limit: 1000 }), // D3: lookup join keeps the full set
      clientesApi.list({ limit: 1000 }), // cliente name join + form options
    ])
    productos.value = productosList.items
    clientes.value = clientesList.items
    total.value = ventasPage.total
    rawVentas.value = ventasPage.items
    const variantes = await fetchVariantesForVentas(
      buildVentaRows(ventasPage.items, productos.value, [], clientes.value),
    )
    rows.value = buildVentaRows(ventasPage.items, productos.value, variantes, clientes.value)
  } catch {
    error.value = 'No se pudo cargar la lista de ventas. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** FE-2: filter changes reset to page 1 and refetch. */
function onFilterChange(): void {
  page.value = 1
  load()
}

/** Paginator @page: recompute the 1-based page from the 0-based first index. */
function onPage(e: { first: number; rows: number }): void {
  page.value = Math.floor(e.first / e.rows) + 1
  load()
}

/** Header column filters (VentasTable) drive the same refs as the toolbar. */
function onTableFilterChange(filters: { canal_venta?: string | null; estado?: string | null }): void {
  filterCanal.value = (filters.canal_venta ?? null) as typeof filterCanal.value
  filterEstado.value = (filters.estado ?? null) as typeof filterEstado.value
  onFilterChange()
}

/** Server-side column sort: reset to page 1; a null order clears the sort. */
function onTableSortChange(sort: { prop: string; order: 'asc' | 'desc' | null }): void {
  sortBy.value = sort.order === null ? null : sort.prop
  sortOrder.value = sort.order
  onFilterChange()
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
function openCreateVenta(): void {
  editingVenta.value = null
  ventaDialogVisible.value = true
}

/** Editar: resolve the full VentaRead from the current page and open the
 *  dialog in edit mode (prefill lives in VentasForm via `initial`). */
function openEditVenta(row: VentaRow): void {
  editingVenta.value = rawVentas.value.find((v) => v.id === row.id) ?? null
  ventaDialogVisible.value = true
}

/** FE-DLG-2/3: closing without saving discards the edit prefill. */
function resetVentaDialog(): void {
  editingVenta.value = null
}

/** MOD-1: POST the VentaCreate payload, confirm and refresh the list. */
async function onSubmit(payload: VentaCreate): Promise<void> {
  saving.value = true
  try {
    await ventasApi.create(payload)
    ElMessage.success('Venta registrada correctamente')
    ventaDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo registrar la venta. Verifica los datos e inténtalo de nuevo.')
  } finally {
    saving.value = false
  }
}

/** T9: one @submit entry — route create vs edit by the dialog mode. */
function submitVenta(payload: VentaCreate): void {
  if (editingVenta.value === null) {
    void onSubmit(payload)
  } else {
    void onSubmitEdit(payload)
  }
}

/** PUT the VentaCreate payload (the edit body equals the create body); the
 *  backend recalcs the total and rebalances stock. */
async function onSubmitEdit(payload: VentaCreate): Promise<void> {
  if (editingVenta.value === null) return
  saving.value = true
  try {
    await ventasApi.update({ venta_id: editingVenta.value.id }, payload)
    ElMessage.success('Venta actualizada correctamente')
    ventaDialogVisible.value = false
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo actualizar la venta. Verifica los datos e inténtalo de nuevo.')
  } finally {
    saving.value = false
  }
}

/** Anular (soft-cancel): confirm first, then DELETE; success restores stock
 *  server-side and refreshes the list. */
async function onAnular(ventaId: number): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `¿Anular la venta #${ventaId}? Se restaurará el stock de los insumos.`,
      'Anular venta',
      {
        type: 'warning',
        confirmButtonText: 'Sí, anular',
        cancelButtonText: 'Cancelar',
      },
    )
  } catch {
    return // user cancelled
  }
  try {
    await ventasApi.anular({ venta_id: ventaId })
    ElMessage.success('Venta anulada correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo anular la venta.')
  }
}

/** Marcar una venta como regalo tras confirmar; recarga la lista al éxito. */
async function onMarcarRegalo(ventaId: number): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `¿Marcar la venta #${ventaId} como regalo? Se conservará el precio como referencia pero no contará como ingreso.`,
      'Marcar como regalo',
      {
        type: 'warning',
        confirmButtonText: 'Sí, marcar',
        cancelButtonText: 'Cancelar',
      },
    )
  } catch {
    return // user cancelled
  }
  try {
    await ventasApi.updateEsRegalo({ venta_id: ventaId }, { es_regalo: true })
    ElMessage.success('Venta marcada como regalo')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo marcar la venta como regalo.')
  }
}

onMounted(load)
</script>

<template>
  <section class="ventas">
    <header class="ventas-header">
      <h2>Ventas</h2>
      <Button :loading="loading" data-test="refresh-ventas" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="ventas-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Listado" name="listado">
        <div class="venta-toolbar">
          <el-select
            v-model="filterCanal"
            clearable
            placeholder="Canal de venta"
            data-test="venta-canal-filter"
            @change="onFilterChange"
          >
            <el-option label="Web" value="web" />
            <el-option label="WhatsApp" value="whatsapp" />
            <el-option label="Instagram" value="instagram" />
            <el-option label="Feria" value="feria" />
          </el-select>
          <el-select
            v-model="filterEstado"
            clearable
            placeholder="Estado"
            data-test="venta-estado-filter"
            @change="onFilterChange"
          >
            <el-option label="Completada" value="completada" />
            <el-option label="Anulada" value="anulada" />
          </el-select>
          <el-select
            v-model="filterProductoId"
            clearable
            filterable
            placeholder="Producto"
            data-test="venta-producto-filter"
            @change="onFilterChange"
          >
            <el-option
              v-for="producto in productos"
              :key="producto.id"
              :label="producto.nombre"
              :value="producto.id"
            />
          </el-select>
          <Button v-if="canRegister" data-test="nueva-venta" @click="openCreateVenta">
            Nueva venta
          </Button>
        </div>
        <VentasTable
          :rows="rows"
          :loading="loading"
          :can-mark-regalo="canRegister"
          @filter-change="onTableFilterChange"
          @sort-change="onTableSortChange"
          @marcar-regalo="onMarcarRegalo"
          @editar="openEditVenta"
          @anular="onAnular"
        />
        <Paginator
          class="tabla-paginacion"
          :total-records="total"
          :rows="pageSize"
          :first="(page - 1) * pageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="onPage"
        />

        <el-dialog
          v-model="ventaDialogVisible"
          :title="editingVenta === null ? 'Nueva venta' : 'Editar venta'"
          :close-on-click-modal="false"
          :close-on-press-escape="!saving"
          :show-close="!saving"
          width="640px"
          @closed="resetVentaDialog"
        >
          <VentasForm
            v-if="ventaDialogVisible"
            :productos="productos"
            :clientes="clientes"
            :load-variantes="loadVariantes"
            :mode="editingVenta === null ? 'create' : 'edit'"
            :initial="editingVenta"
            :saving="saving"
            @submit="submitVenta"
          />
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<style scoped>
.ventas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.ventas-header h2 {
  margin: 0;
}

.ventas-error {
  margin-bottom: 1rem;
}

.venta-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  max-width: 55rem;
  margin-bottom: 1rem;
}

.venta-toolbar .el-select {
  width: 12rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}
</style>
