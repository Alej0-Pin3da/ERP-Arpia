<script setup lang="ts">
/**
 * Monthly sales chart (DASH-1).
 *
 * ECharts bar chart (vue-echarts) over gap-filled months with
 * gradient fills, custom tooltips, and responsive layout.
 */
import { computed } from 'vue'
import Skeleton from 'primevue/skeleton'

import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import * as echarts from 'echarts/core'
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

/** Axis tooltip formatting */
function tooltipFormatter(params: TooltipPoint | TooltipPoint[]): string {
  const point = Array.isArray(params) ? params[0] : params
  return `
    <div style="font-family: Inter, sans-serif; padding: 4px;">
      <div style="font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">
        ${point.axisValueLabel}
      </div>
      <div style="font-size: 14px; font-weight: 700; color: #f8fafc;">
        ${formatMoney(String(point.value))}
      </div>
    </div>
  `
}

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'axis' as const,
    formatter: tooltipFormatter,
    backgroundColor: 'rgba(19, 19, 24, 0.95)',
    borderColor: 'rgba(197, 160, 89, 0.3)',
    borderWidth: 1,
    padding: 8,
    borderRadius: 8,
    extraCssText: 'box-shadow: 0 10px 25px rgba(0, 0, 0, 0.8); backdrop-filter: blur(12px);',
  },
  grid: { left: 16, right: 24, top: 24, bottom: 8, containLabel: true },
  xAxis: {
    type: 'category' as const,
    data: props.rows.map((row) => row.label),
    axisLabel: {
      color: '#a8a29e',
      fontSize: 11,
      fontWeight: 500,
    },
    axisLine: { lineStyle: { color: 'rgba(197, 160, 89, 0.2)' } },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value' as const,
    axisLabel: {
      color: '#78716c',
      fontSize: 11,
      formatter: (val: number) => `$${(val / 1000).toFixed(0)}k`,
    },
    splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)', type: 'dashed' as const } },
  },
  series: [
    {
      name: 'Ventas',
      type: 'bar' as const,
      data: props.rows.map((row) => row.total),
      barMaxWidth: 32,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#dfb15b' },
          { offset: 1, color: '#9e7d3b' },
        ]),
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f3e5ab' },
            { offset: 1, color: '#c5a059' },
          ]),
        },
      },
    },
  ],
}))
</script>

<template>
  <div v-if="loading" class="chart-skeleton">
    <Skeleton v-for="n in 5" :key="n" height="2rem" />
  </div>
  <div v-else-if="rows.length === 0" class="chart-empty">
    <i class="pi pi-chart-bar empty-chart-icon" />
    <span>Sin ventas registradas en el período</span>
  </div>
  <v-chart v-else :option="chartOption" autoresize class="ventas-chart" />
</template>

<style scoped>
.ventas-chart {
  height: 320px;
  width: 100%;
}

.chart-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  height: 320px;
  justify-content: center;
  padding: 1rem;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  height: 320px;
  color: var(--arpia-text-muted);
  font-size: 0.88rem;
}

.empty-chart-icon {
  font-size: 2rem;
  color: var(--arpia-text-faint);
}
</style>
