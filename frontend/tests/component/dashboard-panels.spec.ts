/**
 * Dashboard panel component tests (task 1.9, spec DASH-1..3).
 *
 * Renders each dashboard panel with fixture data and asserts what the user
 * SEES: KPI values formatted es-CO, low-stock severity tags (Crítico/Bajo),
 * margen rows with joined names + fallbacks, and the ECharts option the
 * sales chart receives (vue-echarts mocked — jsdom has no canvas).
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { nextTick, type Component } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import BajoStockTable from '@/components/dashboard/BajoStockTable.vue'
import KpiCards from '@/components/dashboard/KpiCards.vue'
import MargenTable from '@/components/dashboard/MargenTable.vue'
import VentasMensualesChart from '@/components/dashboard/VentasMensualesChart.vue'
import type { FilledMonthRow, MargenRow } from '@/utils/dashboard'
import type { components } from '@/types/api.d'

type InsumoBajoStockRead = components['schemas']['InsumoBajoStockRead']

// jsdom has no canvas — stub vue-echarts with a prop-recording component so
// tests can inspect the option the chart WOULD receive.
const { VChartStub } = vi.hoisted(() => ({
  VChartStub: {
    name: 'VChartStub',
    props: { option: { type: Object, default: () => ({}) } },
    template: '<div class="vchart-stub" />',
  },
}))
vi.mock('vue-echarts', () => ({ default: VChartStub }))

async function mountPanel(component: Component, props: Record<string, unknown>): Promise<VueWrapper> {
  const wrapper = mount(component, { props, global: { plugins: [ElementPlus] } })
  // el-table paints its body one tick after mount (ResizeObserver layout).
  await nextTick()
  return wrapper
}

describe('KpiCards (DASH-1)', () => {
  it('renders month total, quantity and counts formatted es-CO', async () => {
    const wrapper = await mountPanel(KpiCards, {
      monthTotal: '1234567.89',
      monthCount: 42,
      lowStockCount: 3,
      margenCount: 7,
    })

    const text = wrapper.text()
    expect(text).toContain('Ventas del mes')
    expect(text).toContain('$1.234.567,89')
    expect(text).toContain('Unidades vendidas')
    expect(text).toContain('42')
    expect(text).toContain('Insumos bajo stock')
    expect(text).toContain('3')
    expect(text).toContain('Productos con margen')
    expect(text).toContain('7')
  })

  it('renders "$0,00" and "0" when there is no data (empty analytics)', async () => {
    const wrapper = await mountPanel(KpiCards, {
      monthTotal: null,
      monthCount: null,
      lowStockCount: 0,
      margenCount: 0,
    })

    expect(wrapper.text()).toContain('$0,00')
    expect(wrapper.text()).toContain('Productos con margen')
  })

  it('shows a skeleton while loading instead of values', async () => {
    const wrapper = await mountPanel(KpiCards, {
      monthTotal: '5000',
      monthCount: 1,
      lowStockCount: 0,
      margenCount: 0,
      loading: true,
    })

    expect(wrapper.find('.el-skeleton').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('$5.000,00')
  })
})

describe('VentasMensualesChart (DASH-1)', () => {
  const rows: FilledMonthRow[] = [
    { mes: '2026-01', label: 'ene 2026', total: 1000, cantidad: 3 },
    { mes: '2026-02', label: 'feb 2026', total: 0, cantidad: 0 },
    { mes: '2026-03', label: 'mar 2026', total: 2500.5, cantidad: 5 },
  ]

  it('passes the gap-filled months to ECharts as categories with zero bars', async () => {
    const wrapper = await mountPanel(VentasMensualesChart, { rows })

    const option = wrapper.findComponent(VChartStub).props('option')
    expect(option.xAxis.data).toEqual(['ene 2026', 'feb 2026', 'mar 2026'])
    expect(option.series[0].data).toEqual([1000, 0, 2500.5])
    expect(option.series[0].type).toBe('bar')
  })

  it('formats tooltips as es-CO money', async () => {
    const wrapper = await mountPanel(VentasMensualesChart, { rows })

    const option = wrapper.findComponent(VChartStub).props('option')
    const tooltip = option.tooltip.formatter([{ axisValueLabel: 'ene 2026', value: 1000 }])
    expect(tooltip).toContain('ene 2026')
    expect(tooltip).toContain('$1.000,00')
  })

  it('shows an empty state instead of the chart when there are no months', async () => {
    const wrapper = await mountPanel(VentasMensualesChart, { rows: [] })

    expect(wrapper.findComponent(VChartStub).exists()).toBe(false)
    expect(wrapper.text()).toContain('Sin ventas en el período')
  })
})

describe('BajoStockTable (DASH-2)', () => {
  const rows: InsumoBajoStockRead[] = [
    { insumo_id: 1, nombre: 'Harina', unidad_medida: 'kg', stock_actual: '2.0', stock_minimo: '10.0' },
    { insumo_id: 2, nombre: 'Huevo', unidad_medida: 'un', stock_actual: '6', stock_minimo: '10' },
  ]

  it('renders rows with es-CO quantities and severity tags (Crítico/Bajo)', async () => {
    const wrapper = await mountPanel(BajoStockTable, { rows })

    const text = wrapper.text()
    expect(text).toContain('Harina')
    expect(text).toContain('kg')
    expect(text).toContain('Huevo')
    // stock_actual 2 < 50% of 10 -> danger "Crítico"; 6 in [5,10) -> warning "Bajo".
    expect(text).toContain('Crítico')
    expect(text).toContain('Bajo')
  })

  it('shows an empty state when no insumos are below stock', async () => {
    const wrapper = await mountPanel(BajoStockTable, { rows: [] })

    expect(wrapper.text()).toContain('Sin insumos bajo stock')
  })
})

describe('MargenTable (DASH-3)', () => {
  const rows: MargenRow[] = [
    {
      producto_id: 1,
      nombre: 'Arepa de huevo',
      variante: '(base)',
      margen_total: '100000.00',
      margen_promedio: '50000.00',
    },
    {
      producto_id: 99,
      nombre: 'Producto #99',
      variante: 'De carne',
      margen_total: '20000.50',
      margen_promedio: '10000.25',
    },
  ]

  it('renders joined product/variant names with margins formatted es-CO', async () => {
    const wrapper = await mountPanel(MargenTable, { rows })

    const text = wrapper.text()
    expect(text).toContain('Arepa de huevo')
    expect(text).toContain('(base)')
    expect(text).toContain('$100.000,00')
    expect(text).toContain('$50.000,00')
    // DASH-3 fallback labels render as-is.
    expect(text).toContain('Producto #99')
    expect(text).toContain('De carne')
    expect(text).toContain('$20.000,50')
  })

  it('shows an empty state when no margins were computed', async () => {
    const wrapper = await mountPanel(MargenTable, { rows: [] })

    expect(wrapper.text()).toContain('Sin márgenes calculados')
  })
})
