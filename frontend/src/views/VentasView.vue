<script setup lang="ts">
/**
 * Ventas view (tasks 2.1+2.2, spec MOD-1).
 *
 * Two tabs: the sales list and the register form.
 *  - List: GET /ventas is UNBOUNDED server-side, so it is sliced client-side
 *    to the most recent VENTAS_LIST_LIMIT (pagination deferred this phase) and
 *    joined client-side with /productos (limit 1000), their variantes (fetched
 *    ONLY for products present in the sliced ventas) and /clientes names.
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
import {
  VENTAS_LIST_LIMIT,
  buildVentaRows,
  sliceVentas,
  type VentaCreate,
  type VentaRow,
} from '@/utils/ventas'
import type {
  ClienteRead,
  ProductoRead,
  VentaRead,
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
const productos = ref<ProductoRead[]>([])
const clientes = ref<ClienteRead[]>([])

/** Variante fetcher handed to the form (productosApi.listVariantes). */
async function loadVariantes(productoId: number): Promise<VarianteProductoRead[]> {
  return productosApi.listVariantes({ producto_id: productoId })
}

/** Variantes for the list join — only for products that have detail rows. */
async function fetchVariantesForVentas(ventas: VentaRead[]): Promise<VarianteProductoRead[]> {
  const ids = [...new Set(ventas.flatMap((v) => v.detalles.map((d) => d.producto_id)))]
  const lists = await Promise.all(ids.map((producto_id) => productosApi.listVariantes({ producto_id })))
  return lists.flat()
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [ventas, productosList, clientesList] = await Promise.all([
      ventasApi.list(),
      productosApi.list({ limit: 1000 }),
      clientesApi.list(),
    ])
    productos.value = productosList
    clientes.value = clientesList
    const sliced = sliceVentas(ventas, VENTAS_LIST_LIMIT)
    const variantes = await fetchVariantesForVentas(sliced)
    rows.value = buildVentaRows(sliced, productosList, variantes, clientesList)
  } catch {
    error.value = 'No se pudo cargar la lista de ventas. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
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
        <p class="list-note">
          Mostrando las últimas {{ VENTAS_LIST_LIMIT }} ventas (el listado del servidor no está
          paginado).
        </p>
        <VentasTable :rows="rows" :loading="loading" />
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

.list-note {
  margin: 0 0 0.75rem;
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
}
</style>
