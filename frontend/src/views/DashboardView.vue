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
 */
import { computed, onMounted, ref } from 'vue'

import { analiticosApi, productosApi } from '@/api/endpoints'
import BajoStockTable from '@/components/dashboard/BajoStockTable.vue'
import KpiCards from '@/components/dashboard/KpiCards.vue'
import MargenTable from '@/components/dashboard/MargenTable.vue'
import VentasMensualesChart from '@/components/dashboard/VentasMensualesChart.vue'
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
    margenRows.value = buildMargenRows(margenes, productos, variantes)
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
      <el-button :loading="loading" data-test="refresh-dashboard" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="dashboard-error"
    />

    <KpiCards
      :month-total="monthSummary?.total ?? null"
      :month-count="monthSummary?.cantidad ?? null"
      :low-stock-count="lowStockCount"
      :margen-count="margenCount"
      :loading="loading"
    />

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="panel-card">
          <template #header>Ventas por mes</template>
          <VentasMensualesChart :rows="chartRows" :loading="loading" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="panel-card">
          <template #header>Insumos bajo stock</template>
          <BajoStockTable :rows="bajoStock" :loading="loading" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel-card">
      <template #header>Márgenes por producto</template>
      <MargenTable :rows="margenRows" :loading="loading" />
    </el-card>
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

.panel-card {
  margin-bottom: 1rem;
}
</style>
