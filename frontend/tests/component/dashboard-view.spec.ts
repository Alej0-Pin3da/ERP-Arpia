/**
 * Dashboard view integration tests (task 1.9, spec DASH-1..3).
 *
 * Mounts the REAL DashboardView + its four panels against a mocked API
 * module: KPIs computed from the last ventas-mensuales row, the chart
 * receiving gap-filled months, both tables populated with joined/severity
 * data, and the loading/error/refresh lifecycle.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { describe, expect, it, vi } from 'vitest'

import DashboardView from '@/views/DashboardView.vue'

// jsdom has no canvas — stub vue-echarts (the view renders the real chart).
const { VChartStub } = vi.hoisted(() => ({
  VChartStub: {
    name: 'VChartStub',
    props: { option: { type: Object, default: () => ({}) } },
    template: '<div class="vchart-stub" />',
  },
}))
vi.mock('vue-echarts', () => ({ default: VChartStub }))

// Mock the HTTP layer: the view orchestrates analiticos + productos calls.
const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    ventasMensuales: vi.fn(),
    insumosBajoStock: vi.fn(),
    margenPorProducto: vi.fn(),
    listProductos: vi.fn(),
    listVariantes: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  analiticosApi: {
    ventasMensuales: apiMocks.ventasMensuales,
    insumosBajoStock: apiMocks.insumosBajoStock,
    margenPorProducto: apiMocks.margenPorProducto,
  },
  productosApi: {
    list: apiMocks.listProductos,
    listVariantes: apiMocks.listVariantes,
  },
}))

const VENTAS = [
  { mes: '2026-01-01', total: '1000.00', cantidad: 3 },
  { mes: '2026-03-01', total: '2500.50', cantidad: 5 },
]
const BAJO_STOCK = [
  { insumo_id: 1, nombre: 'Harina', unidad_medida: 'kg', stock_actual: '2.0', stock_minimo: '10.0' },
]
const MARGENES = [
  { producto_id: 1, variante_id: null, margen_total: '100000.00', margen_promedio: '50000.00' },
  { producto_id: 99, variante_id: null, margen_total: '20000.00', margen_promedio: '10000.00' },
]
const PRODUCTOS = [
  {
    id: 1,
    tipo_producto_id: 1,
    nombre: 'Arepa de huevo',
    requiere_fabricacion: true,
    costos_operativos_fijos: '0',
    precio_venta_sugerido: '5000',
  },
]

async function mountDashboard(): Promise<VueWrapper> {
  const wrapper = mount(DashboardView, { global: { plugins: [ElementPlus] } })
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('DashboardView (DASH-1..3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMocks.ventasMensuales.mockResolvedValue(VENTAS)
    apiMocks.insumosBajoStock.mockResolvedValue(BAJO_STOCK)
    apiMocks.margenPorProducto.mockResolvedValue(MARGENES)
    // The list contract is now {items, total} — the view joins on `.items`.
    apiMocks.listProductos.mockResolvedValue({ items: PRODUCTOS, total: PRODUCTOS.length })
    apiMocks.listVariantes.mockResolvedValue([])
  })

  it('renders KPIs from the last month, gap-filled chart and both tables', async () => {
    const wrapper = await mountDashboard()

    const text = wrapper.text()
    // KPI: last row (mar) formatted es-CO; counts from endpoint lengths.
    expect(text).toContain('$2.500,50')
    expect(text).toContain('Insumos bajo stock')
    expect(text).toContain('Productos con margen')

    // Chart receives gap-filled months (feb zeroed).
    const option = wrapper.findComponent(VChartStub).props('option')
    expect(option.xAxis.data).toEqual(['ene 2026', 'feb 2026', 'mar 2026'])
    expect(option.series[0].data).toEqual([1000, 0, 2500.5])

    // Low-stock table row + severity; margen table join + fallback.
    expect(text).toContain('Harina')
    expect(text).toContain('Crítico')
    expect(text).toContain('Arepa de huevo')
    expect(text).toContain('(base)')
    expect(text).toContain('Producto #99')
    expect(text).toContain('$100.000,00')
  })

  it('fetches variantes only for the products present in margen rows', async () => {
    await mountDashboard()

    // Distinct margen producto_ids [1, 99] -> exactly two variante calls.
    expect(apiMocks.listVariantes).toHaveBeenCalledTimes(2)
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 1 })
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 99 })
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 1000 })
  })

  it('shows zeroed KPIs and empty states when the API returns no data', async () => {
    apiMocks.ventasMensuales.mockResolvedValue([])
    apiMocks.insumosBajoStock.mockResolvedValue([])
    apiMocks.margenPorProducto.mockResolvedValue([])

    const wrapper = await mountDashboard()

    const text = wrapper.text()
    expect(text).toContain('$0,00')
    expect(text).toContain('Sin ventas en el período')
    expect(text).toContain('Sin insumos bajo stock')
    expect(text).toContain('Sin márgenes calculados')
    expect(wrapper.findComponent(VChartStub).exists()).toBe(false)
  })

  it('surfaces an error banner when the analytics calls fail', async () => {
    apiMocks.ventasMensuales.mockRejectedValue(new Error('network down'))

    const wrapper = await mountDashboard()

    expect(wrapper.text()).toContain('No se pudo cargar el tablero')
  })

  it('reloads all panels when the refresh button is clicked', async () => {
    const wrapper = await mountDashboard()
    expect(apiMocks.ventasMensuales).toHaveBeenCalledTimes(1)

    const refreshButton = wrapper.findAll('button').find((b) => b.text().includes('Actualizar'))
    await refreshButton!.trigger('click')
    await flushPromises()

    expect(apiMocks.ventasMensuales).toHaveBeenCalledTimes(2)
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2)
  })
})
