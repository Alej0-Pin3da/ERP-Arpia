<script setup lang="ts">
/**
 * Monthly finanzas trend chart (ANA-6, Análisis screen).
 *
 * ECharts grouped bar chart (vue-echarts) over the gap-filled months from
 * finanzas-mensuales (fillFinanzasMonths output): every calendar month between
 * first and last appears on the axis with an Ingresos bar and a Gastos bar;
 * missing months render as zero bars. Tooltips are es-CO money.
 */
import { computed } from 'vue'
import Skeleton from 'primevue/skeleton'

import { BarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

import { formatMoney } from '@/utils/format'
import type { FinanzasMonthRow } from '@/utils/dashboard'

use([BarChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  /** Gap-filled months (fillFinanzasMonths output). */
  rows: FinanzasMonthRow[]
  loading?: boolean
}>()

interface TooltipPoint {
  axisValueLabel: string
  value: unknown
  seriesName?: string
}

/** Axis tooltip: "ene 2026\nIngresos: $1.000,00\nGastos: $500,00". */
function tooltipFormatter(params: TooltipPoint | TooltipPoint[]): string {
  const points = Array.isArray(params) ? params : [params]
  const first = points[0]
  const lines = points
    .filter((p) => p.value !== null && p.value !== undefined && String(p.value) !== '')
    .map((p) => `${p.seriesName ?? ''}: ${formatMoney(String(p.value))}`)
  return first ? `${first.axisValueLabel}\n${lines.join('\n')}` : ''
}

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'axis' as const,
    formatter: tooltipFormatter,
  },
  legend: {
    data: ['Ingresos', 'Gastos'],
    textStyle: { color: 'rgba(255, 255, 255, 0.75)' },
  },
  grid: { left: 16, right: 24, top: 40, bottom: 8, containLabel: true },
  xAxis: {
    type: 'category' as const,
    data: props.rows.map((row) => row.label),
    axisLabel: { color: 'rgba(255, 255, 255, 0.65)' },
    axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value' as const,
    axisLabel: { color: 'rgba(255, 255, 255, 0.65)' },
    splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } },
  },
  series: [
    {
      name: 'Ingresos',
      type: 'bar' as const,
      data: props.rows.map((row) => row.ingresos),
      itemStyle: { color: 'var(--arpia-success, #67c23a)', borderRadius: [4, 4, 0, 0] },
    },
    {
      name: 'Gastos',
      type: 'bar' as const,
      data: props.rows.map((row) => row.gastos),
      itemStyle: { color: 'var(--arpia-danger, #f56c6c)', borderRadius: [4, 4, 0, 0] },
    },
  ],
}))
</script>

<template>
  <div v-if="loading" class="chart-skeleton">
    <Skeleton v-for="n in 5" :key="n" />
  </div>
  <div v-else-if="rows.length === 0" class="chart-empty">Sin datos en el período</div>
  <v-chart v-else :option="chartOption" autoresize class="finanzas-chart" />
</template>

<style scoped>
.finanzas-chart {
  height: 320px;
  width: 100%;
}

.chart-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  height: 320px;
  justify-content: center;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 320px;
  color: var(--arpia-text-muted);
  font-size: 0.9rem;
}
</style>