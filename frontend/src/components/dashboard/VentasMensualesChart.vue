<script setup lang="ts">
/**
 * Monthly sales chart (task 1.9, spec DASH-1).
 *
 * ECharts bar chart (vue-echarts) over the gap-filled months from
 * ventas-mensuales: every calendar month between first and last appears on
 * the axis, missing months render as zero bars. Tooltips are es-CO money.
 */
import { computed } from 'vue'

import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

import { formatMoney } from '@/utils/format'
import type { FilledMonthRow } from '@/utils/dashboard'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  /** Gap-filled months (fillMissingMonths output). */
  rows: FilledMonthRow[]
  loading?: boolean
}>()

interface TooltipPoint {
  axisValueLabel: string
  value: unknown
}

/** Axis tooltip: "ene 2026: $1.000,00" — es-CO money, no axis clutter. */
function tooltipFormatter(params: TooltipPoint | TooltipPoint[]): string {
  const point = Array.isArray(params) ? params[0] : params
  return `${point.axisValueLabel}: ${formatMoney(String(point.value))}`
}

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'axis' as const,
    formatter: tooltipFormatter,
  },
  grid: { left: 16, right: 24, top: 24, bottom: 8, containLabel: true },
  xAxis: {
    type: 'category' as const,
    data: props.rows.map((row) => row.label),
  },
  yAxis: { type: 'value' as const },
  series: [
    {
      name: 'Ventas',
      type: 'bar' as const,
      data: props.rows.map((row) => row.total),
      itemStyle: { color: 'var(--el-color-primary, #409eff)' },
    },
  ],
}))
</script>

<template>
  <el-skeleton v-if="loading" :rows="5" animated />
  <el-empty v-else-if="rows.length === 0" description="Sin ventas en el período" :image-size="80" />
  <v-chart v-else :option="chartOption" autoresize class="ventas-chart" />
</template>

<style scoped>
.ventas-chart {
  height: 320px;
  width: 100%;
}
</style>
