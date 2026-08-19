<script setup lang="ts">
/**
 * Dashboard view (task 1.9, spec DASH-1..3).
 *
 * Orchestrates the analytics endpoints into the four panels:
 *  - KPI cards from the last ventas-mensuales row + endpoint lengths
 *  - monthly sales chart with missing months zero-filled
 *  - low-stock insumos table with severity highlighting
 *  - margen table joined client-side with /productos + /variantes
 *    (variantes fetched ONLY for the products that appear in margen rows —
 *    the payload is ID-only, so a full product scan is not needed).
 * One refresh button reloads everything; failures surface as an alert.
 *
 * Slice 5 (MIG-2): el-row/el-col/el-card replaced by a scoped CSS grid and
 * PrimeVue Card panels (same responsive behavior, no EP dependency).
 */
import { computed, onMounted, ref } from 'vue'

import { analiticosApi, productosApi } from '@/api/endpoints'
import BajoStockTable from '@/components/dashboard/BajoStockTable.vue'
import KpiCards from '@/components/dashboard/KpiCards.vue'
import MargenTable from '@/components/dashboard/MargenTable.vue'
import VentasMensualesChart from '@/components/dashboard/VentasMensualesChart.vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import {
  buildMargenRows,
  fillMissingMonths,
  lastMonthSummary,
  type MargenRow,
} from '@/utils/dashboard'
import type {
  InsumoBajoStockRead,
  MargenProductoRead,
  VarianteProductoRead,
  VentasMensualesRead,
} from '@/types/api.d'

const loading = ref(false)
const error = ref<string | null>(null)
const ventasMensuales = ref<VentasMensualesRead[]>([])
const bajoStock = ref<InsumoBajoStockRead[]>([])
const margenRows = ref<MargenRow[]>([])

const chartRows = computed(() => fillMissingMonths(ventasMensuales.value))
const monthSummary = computed(() => lastMonthSummary(ventasMensuales.value))
const lowStockCount = computed(() => bajoStock.value.length)
const margenCount = computed(() => margenRows.value.length)

/** Variante labels for the margen join — only for products that have rows. */
async function fetchVariantesForMargenes(margenes: MargenProductoRead[]): Promise<VarianteProductoRead[]> {
  const ids = [...new Set(margenes.map((m) => m.producto_id))]
  const lists = await Promise.all(ids.map((producto_id) => productosApi.listVariantes({ producto_id })))
  return lists.flat()
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [ventas, stock, margenes, productos] = await Promise.all([
      analiticosApi.ventasMensuales(),
      analiticosApi.insumosBajoStock(),
      analiticosApi.margenPorProducto(),
      productosApi.list({ limit: 1000 }),
    ])
    ventasMensuales.value = ventas
    bajoStock.value = stock
    const variantes = await fetchVariantesForMargenes(margenes)
    // productos is now Paginated<...> — the lookup join uses `.items` (D10).
    margenRows.value = buildMargenRows(margenes, productos.items, variantes)
  } catch {
    error.value = 'No se pudo cargar el tablero. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="dashboard">
    <header class="dashboard-header">
      <h2>Dashboard</h2>
      <Button :loading="loading" data-test="refresh-dashboard" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="dashboard-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <KpiCards
      :month-total="monthSummary?.total ?? null"
      :month-count="monthSummary?.cantidad ?? null"
      :low-stock-count="lowStockCount"
      :margen-count="margenCount"
      :loading="loading"
    />

    <div class="dashboard-grid">
      <div>
        <Card class="panel-card">
          <template #title>Ventas por mes</template>
          <template #content>
          <VentasMensualesChart :rows="chartRows" :loading="loading" />
          </template>
        </Card>
      </div>
      <div>
        <Card class="panel-card">
          <template #title>Insumos bajo stock</template>
          <template #content>
          <BajoStockTable :rows="bajoStock" :loading="loading" />
          </template>
        </Card>
      </div>
    </div>

    <Card class="panel-card">
      <template #title>Márgenes por producto</template>
      <template #content>
      <MargenTable :rows="margenRows" :loading="loading" />
      </template>
    </Card>
  </section>
</template>

<style scoped>
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.dashboard-header h2 {
  margin: 0;
}

.dashboard-error {
  margin-bottom: 1rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

@media (min-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.panel-card {
  margin-bottom: 1rem;
}
</style>
