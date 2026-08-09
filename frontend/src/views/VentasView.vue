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
import { ElMessage } from 'element-plus'

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
const productos = ref<ProductoRead[]>([])
const clientes = ref<ClienteRead[]>([])

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
          filtros: { canal_venta: filterCanal.value, estado: filterEstado.value },
        }),
      ),
      productosApi.list({ limit: 1000 }), // D3: lookup join keeps the full set
      clientesApi.list({ limit: 1000 }), // cliente name join + form options
    ])
    productos.value = productosList.items
    clientes.value = clientesList.items
    total.value = ventasPage.total
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

/** MOD-1: POST the VentaCreate payload, confirm and refresh the list. */
async function onSubmit(payload: VentaCreate): Promise<void> {
  saving.value = true
  try {
    await ventasApi.create(payload)
    ElMessage.success('Venta registrada correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo registrar la venta. Verifica los datos e inténtalo de nuevo.')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="ventas">
    <header class="ventas-header">
      <h2>Ventas</h2>
      <el-button :loading="loading" data-test="refresh-ventas" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="ventas-error"
    />

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
        </div>
        <VentasTable :rows="rows" :loading="loading" />
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

      <el-tab-pane v-if="canRegister" label="Registrar venta" name="registrar">
        <VentasForm
          :productos="productos"
          :clientes="clientes"
          :load-variantes="loadVariantes"
          :saving="saving"
          @submit="onSubmit"
        />
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
  gap: 0.75rem;
  max-width: 42rem;
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
