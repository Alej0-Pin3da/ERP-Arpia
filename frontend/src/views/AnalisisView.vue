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
 *
 * Slice 5 (MIG-2): el-row/el-col/el-card replaced by a scoped CSS grid and
 * PrimeVue Card panels (same responsive behavior, no EP dependency).
 */
import { computed, onMounted, ref } from 'vue'

import { analiticosApi, productosApi } from '@/api/endpoints'
import FinanzasMensualesChart from '@/components/dashboard/FinanzasMensualesChart.vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { fillFinanzasMonths, type FinanzasMonthRow } from '@/utils/dashboard'
import { formatDate, formatMoney, formatQty, parseDecimal } from '@/utils/format'
import type { AnaliticosPeriodo, AnaliticosResumen } from '@/api/types'
import type { components } from '@/types/api.d'

type FinanzasMensualesRead = components['schemas']['FinanzasMensualesRead']
type MargenProductoRead = components['schemas']['MargenProductoRead']
type ProductoRead = components['schemas']['ProductoRead']
type TopInsumoRead = components['schemas']['TopInsumoRead']
type TopProductoRead = components['schemas']['TopProductoRead']

const loading = ref(false)
const error = ref<string | null>(null)
const topProductos = ref<TopProductoRead[]>([])
const topInsumos = ref<TopInsumoRead[]>([])
const finanzas = ref<FinanzasMensualesRead[]>([])
const margenes = ref<MargenProductoRead[]>([])
const productos = ref<ProductoRead[]>([])
const resumen = ref<AnaliticosResumen | null>(null)
const periodo = ref<'12m' | 'year' | 'custom'>('12m')
const customDesde = ref<Date | null>(null)
const customHasta = ref<Date | null>(null)

const periodoOptions = [
  { label: 'Últimos 12 meses', value: '12m' },
  { label: 'Año actual', value: 'year' },
  { label: 'Periodo personalizado', value: 'custom' },
]

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

function isoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function currentPeriod(): AnaliticosPeriodo {
  const today = new Date()
  if (periodo.value === 'custom') {
    if (!customDesde.value || !customHasta.value) return {}
    return { desde: isoDate(customDesde.value), hasta: isoDate(customHasta.value) }
  }
  if (periodo.value === 'year') {
    return { desde: `${today.getFullYear()}-01-01`, hasta: isoDate(today) }
  }
  const desde = new Date(today)
  desde.setFullYear(today.getFullYear() - 1)
  return { desde: isoDate(desde), hasta: isoDate(today) }
}

function variation(current: string, previous: string): string {
  const currentValue = parseDecimal(current) ?? 0
  const previousValue = parseDecimal(previous) ?? 0
  if (previousValue === 0) return currentValue === 0 ? 'Sin variación' : 'Nuevo periodo'
  const percentage = ((currentValue - previousValue) / Math.abs(previousValue)) * 100
  return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(1).replace('.', ',')}% vs anterior`
}

const kpis = computed(() => {
  if (!resumen.value) return []
  return [
    { label: 'Ventas del periodo', value: formatMoney(resumen.value.ventas_total), delta: variation(resumen.value.ventas_total, resumen.value.ventas_periodo_anterior), positive: parseDecimal(resumen.value.ventas_total)! >= parseDecimal(resumen.value.ventas_periodo_anterior)! },
    { label: 'Ticket promedio', value: formatMoney(resumen.value.ticket_promedio), delta: variation(resumen.value.ticket_promedio, resumen.value.ticket_periodo_anterior), positive: parseDecimal(resumen.value.ticket_promedio)! >= parseDecimal(resumen.value.ticket_periodo_anterior)! },
    { label: 'Unidades vendidas', value: formatQty(resumen.value.unidades_vendidas), delta: variation(resumen.value.unidades_vendidas, resumen.value.unidades_periodo_anterior), positive: parseDecimal(resumen.value.unidades_vendidas)! >= parseDecimal(resumen.value.unidades_periodo_anterior)! },
    { label: 'Margen total', value: formatMoney(resumen.value.margen_total), delta: variation(resumen.value.margen_total, resumen.value.margen_periodo_anterior), positive: parseDecimal(resumen.value.margen_total)! >= parseDecimal(resumen.value.margen_periodo_anterior)! },
    { label: 'Gastos', value: formatMoney(resumen.value.gastos_total), delta: variation(resumen.value.gastos_total, resumen.value.gastos_periodo_anterior), positive: parseDecimal(resumen.value.gastos_total)! <= parseDecimal(resumen.value.gastos_periodo_anterior)! },
    { label: 'Resultado neto', value: formatMoney(resumen.value.resultado_neto), delta: variation(resumen.value.resultado_neto, resumen.value.resultado_periodo_anterior), positive: parseDecimal(resumen.value.resultado_neto)! >= parseDecimal(resumen.value.resultado_periodo_anterior)! },
  ]
})

const margenRows = computed(() => {
  const productosById = new Map(productos.value.map((p) => [p.id, p]))
  return margenes.value.map((row) => ({
    producto: productosById.get(row.producto_id)?.nombre ?? `Producto #${row.producto_id}`,
    variante: row.variante_id === null ? 'General' : `Variante #${row.variante_id}`,
    margenTotal: row.margen_total,
    margenPromedio: row.margen_promedio,
  }))
})

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const params = currentPeriod()
    const [summary, topProd, topIns, fin, marg, prods] = await Promise.all([
      analiticosApi.resumen(params),
      analiticosApi.topProductos(params),
      analiticosApi.topInsumos(params),
      analiticosApi.finanzasMensuales(params),
      analiticosApi.margenPorProducto(params),
      productosApi.list({ limit: 1000 }),
    ])
    resumen.value = summary
    topProductos.value = topProd
    topInsumos.value = topIns
    finanzas.value = fin
    margenes.value = marg
    // productos is now Paginated<...> — the lookup join uses `.items` (D10).
    productos.value = prods.items
  } catch {
    error.value = 'No se pudo cargar el análisis. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

function onPeriodChange(): void {
  if (periodo.value !== 'custom' || (customDesde.value && customHasta.value)) void load()
}

onMounted(load)
</script>

<template>
  <section class="analisis">
    <header class="analisis-header">
      <h2>Análisis</h2>
      <div class="analisis-actions">
        <Select
          v-model="periodo"
          :options="periodoOptions"
          option-label="label"
          option-value="value"
          aria-label="Periodo de análisis"
          data-test="analisis-periodo"
          @change="onPeriodChange"
        />
        <DatePicker
          v-if="periodo === 'custom'"
          v-model="customDesde"
          date-format="yy-mm-dd"
          show-icon
          placeholder="Desde"
          aria-label="Fecha inicial"
          @date-select="onPeriodChange"
        />
        <DatePicker
          v-if="periodo === 'custom'"
          v-model="customHasta"
          date-format="yy-mm-dd"
          show-icon
          placeholder="Hasta"
          aria-label="Fecha final"
          @date-select="onPeriodChange"
        />
        <Button icon="pi pi-refresh" :loading="loading" data-test="refresh-analisis" @click="load">
          Actualizar
        </Button>
      </div>
    </header>

    <p v-if="resumen" class="analisis-periodo-label">
      {{ formatDate(resumen.desde) }} - {{ formatDate(resumen.hasta) }} · Comparado con el periodo anterior
    </p>

    <div v-if="error" class="analisis-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <div class="analisis-kpis">
      <Card v-for="kpi in kpis" :key="kpi.label" class="analisis-kpi">
        <template #content>
          <p class="analisis-kpi__label">{{ kpi.label }}</p>
          <p class="analisis-kpi__value">{{ kpi.value }}</p>
          <small :class="['analisis-kpi__delta', { 'analisis-kpi__delta--positive': kpi.positive }]">
            {{ kpi.delta }}
          </small>
        </template>
      </Card>
    </div>

    <div class="analisis-grid">
      <div>
        <Card class="panel-card">
          <template #title>Productos más vendidos</template>
          <template #content>
          <DataTable :value="topProductoRows" :loading="loading" scrollable scroll-height="400px">
            <Column field="nombre" header="Producto" style="min-width: 180px" />
            <Column header="Unidades" style="width: 110px" align="right">
              <template #body="{ data }">{{ parseDecimal(data.unidades) }}</template>
            </Column>
            <Column header="Ingresos" style="width: 150px" align="right">
              <template #body="{ data }">{{ formatMoney(data.ingresos) }}</template>
            </Column>
            <template #empty>
              <div class="analisis-empty">Sin ventas registradas</div>
            </template>
          </DataTable>
          </template>
        </Card>
      </div>
      <div>
        <Card class="panel-card">
          <template #title>Insumos más comprados</template>
          <template #content>
          <DataTable :value="topInsumos" :loading="loading" scrollable scroll-height="400px">
            <Column field="nombre" header="Insumo" style="min-width: 180px" />
            <Column field="unidad_medida" header="Unidad" style="width: 100px" />
            <Column header="Cantidad usada" style="width: 140px" align="right">
              <template #body="{ data }">{{ parseDecimal(data.cantidad) }}</template>
            </Column>
            <template #empty>
              <div class="analisis-empty">Sin compras de insumos</div>
            </template>
          </DataTable>
          </template>
        </Card>
      </div>
    </div>

    <Card class="panel-card">
      <template #title>Rentabilidad por producto</template>
      <template #content>
      <DataTable :value="margenRows" :loading="loading" scrollable scroll-height="400px">
        <Column field="producto" header="Producto" style="min-width: 220px" />
        <Column field="variante" header="Variante" style="min-width: 140px" />
        <Column header="Margen total" style="width: 150px" align="right">
          <template #body="{ data }">{{ formatMoney(data.margenTotal) }}</template>
        </Column>
        <Column header="Margen promedio" style="width: 170px" align="right">
          <template #body="{ data }">{{ formatMoney(data.margenPromedio) }}</template>
        </Column>
        <template #empty>
          <div class="analisis-empty">Sin datos de margen</div>
        </template>
      </DataTable>
      </template>
    </Card>

    <Card class="panel-card">
      <template #title>Tendencia mensual de finanzas</template>
      <template #content>
      <FinanzasMensualesChart :rows="chartRows" :loading="loading" />
      </template>
    </Card>
  </section>
</template>

<style scoped>
.analisis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.analisis-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
}

.analisis-actions :deep(.p-select),
.analisis-actions :deep(.p-datepicker) {
  min-width: 11rem;
}

.analisis-periodo-label {
  margin: -0.5rem 0 1rem;
  color: var(--arpia-text-muted);
  font-size: 0.85rem;
}

.analisis-kpis {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.analisis-kpi {
  border: 1px solid var(--arpia-border);
  border-radius: var(--arpia-radius);
  box-shadow: none;
}

.analisis-kpi__label {
  margin: 0 0 0.35rem;
  color: var(--arpia-gold);
  font-family: var(--arpia-font-heading);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.analisis-kpi__value {
  margin: 0 0 0.35rem;
  color: var(--arpia-text-primary);
  font-family: var(--arpia-font-heading);
  font-size: 1.35rem;
  font-weight: 600;
}

.analisis-kpi__delta {
  color: var(--arpia-danger);
  font-size: 0.75rem;
}

.analisis-kpi__delta--positive {
  color: var(--arpia-success);
}

.analisis-header h2 {
  margin: 0;
}

.analisis-error {
  margin-bottom: 1rem;
}

.analisis-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

@media (min-width: 992px) {
  .analisis-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (min-width: 640px) {
  .analisis-kpis {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1200px) {
  .analisis-kpis {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 767px) {
  .analisis-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.75rem;
  }

  .analisis-actions {
    width: 100%;
    justify-content: stretch;
  }

  .analisis-actions :deep(.p-select),
  .analisis-actions :deep(.p-datepicker),
  .analisis-actions :deep(.p-button) {
    width: 100%;
  }
}

.panel-card {
  margin-bottom: 1rem;
}

.analisis-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>