<script setup lang="ts">
/**
 * Análisis view (ANA-4..6).
 *
 * Orchestrates the analytics endpoints into three read-only panels:
 *  - "Productos más vendidos": top-productos table (unidades + ingresos),
 *    product names joined client-side with /productos (ID-only payload).
 *  - "Insumos más usados": top-insumos table (names come inline from the API).
 *  - "Tendencia mensual de finanzas": finanzas-mensuales grouped bar chart
 *    (ingresos vs gastos), months zero-filled between first and last.
 * Mirrors DashboardView: one refresh button reloads everything; failures
 * surface as an alert. Audited for admin|operador|consulta.
 */
import { computed, onMounted, ref } from 'vue'

import { analiticosApi, productosApi } from '@/api/endpoints'
import FinanzasMensualesChart from '@/components/dashboard/FinanzasMensualesChart.vue'
import { fillFinanzasMonths, type FinanzasMonthRow } from '@/utils/dashboard'
import { formatMoney, parseDecimal } from '@/utils/format'
import type {
  FinanzasMensualesRead,
  ProductoRead,
  TopInsumoRead,
  TopProductoRead,
} from '@/types/api.d'

const loading = ref(false)
const error = ref<string | null>(null)
const topProductos = ref<TopProductoRead[]>([])
const topInsumos = ref<TopInsumoRead[]>([])
const finanzas = ref<FinanzasMensualesRead[]>([])
const productos = ref<ProductoRead[]>([])

/** Top-product rows: product name joined client-side, degraded fallback. */
const topProductoRows = computed(() => {
  const productosById = new Map(productos.value.map((p) => [p.id, p]))
  return topProductos.value.map((row) => ({
    id: row.producto_id,
    nombre: productosById.get(row.producto_id)?.nombre ?? `Producto #${row.producto_id}`,
    unidades: row.unidades,
    ingresos: row.ingresos,
  }))
})

const chartRows = computed<FinanzasMonthRow[]>(() => fillFinanzasMonths(finanzas.value))

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [topProd, topIns, fin, prods] = await Promise.all([
      analiticosApi.topProductos(),
      analiticosApi.topInsumos(),
      analiticosApi.finanzasMensuales(),
      productosApi.list({ limit: 1000 }),
    ])
    topProductos.value = topProd
    topInsumos.value = topIns
    finanzas.value = fin
    // productos is now Paginated<...> — the lookup join uses `.items` (D10).
    productos.value = prods.items
  } catch {
    error.value = 'No se pudo cargar el análisis. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="analisis">
    <header class="analisis-header">
      <h2>Análisis</h2>
      <el-button :loading="loading" data-test="refresh-analisis" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="analisis-error"
    />

    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="panel-card">
          <template #header>Productos más vendidos</template>
          <el-table :data="topProductoRows" v-loading="loading" max-height="400">
            <el-table-column prop="nombre" label="Producto" min-width="180" />
            <el-table-column label="Unidades" width="110" align="right">
              <template #default="{ row }">{{ parseDecimal(row.unidades) }}</template>
            </el-table-column>
            <el-table-column label="Ingresos" width="150" align="right">
              <template #default="{ row }">{{ formatMoney(row.ingresos) }}</template>
            </el-table-column>
            <template #empty>
              <el-empty description="Sin ventas registradas" :image-size="80" />
            </template>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="panel-card">
          <template #header>Insumos más usados</template>
          <el-table :data="topInsumos" v-loading="loading" max-height="400">
            <el-table-column prop="nombre" label="Insumo" min-width="180" />
            <el-table-column prop="unidad_medida" label="Unidad" width="100" />
            <el-table-column label="Cantidad usada" width="140" align="right">
              <template #default="{ row }">{{ parseDecimal(row.cantidad) }}</template>
            </el-table-column>
            <template #empty>
              <el-empty description="Sin compras de insumos" :image-size="80" />
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel-card">
      <template #header>Tendencia mensual de finanzas</template>
      <FinanzasMensualesChart :rows="chartRows" :loading="loading" />
    </el-card>
  </section>
</template>

<style scoped>
.analisis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.analisis-header h2 {
  margin: 0;
}

.analisis-error {
  margin-bottom: 1rem;
}

.panel-card {
  margin-bottom: 1rem;
}
</style>