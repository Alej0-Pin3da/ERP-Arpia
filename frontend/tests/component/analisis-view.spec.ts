/**
 * AnalisisView integration tests (ANA-4..6).
 *
 * Mounts the REAL AnalisisView against a mocked analytics API: the two direct
 * panels ("Productos más vendidos" / "Insumos más usados") are PrimeVue
 * DataTables (slice 1b) rendering the joined top-product names (with the
 * 'Producto #id' fallback), es-CO money/qty, and empty states; failures
 * surface as an alert. The monthly chart is stub-rendered (jsdom has no
 * canvas — vue-echarts mocked like dashboard-panels.spec).
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import AnalisisView from '@/views/AnalisisView.vue'
import type { components } from '@/types/api.d'

type TopProductoRead = components['schemas']['TopProductoRead']
type TopInsumoRead = components['schemas']['TopInsumoRead']
type MargenProductoRead = components['schemas']['MargenProductoRead']

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    topProductos: vi.fn(),
    topInsumos: vi.fn(),
    margenPorProducto: vi.fn(),
    finanzasMensuales: vi.fn(),
    resumen: vi.fn(),
    listProductos: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  analiticosApi: {
    topProductos: apiMocks.topProductos,
    topInsumos: apiMocks.topInsumos,
    margenPorProducto: apiMocks.margenPorProducto,
    finanzasMensuales: apiMocks.finanzasMensuales,
    resumen: apiMocks.resumen,
  },
  productosApi: { list: apiMocks.listProductos },
}))
// jsdom has no canvas — the monthly chart only needs to mount (like dashboard-panels).
vi.mock('vue-echarts', () => ({ default: { name: 'VChartStub', template: '<div />' } }))

const TOP_PRODUCTOS: TopProductoRead[] = [
  { producto_id: 1, unidades: '12.00', ingresos: '150000.00' },
]
const TOP_INSUMOS: TopInsumoRead[] = [
  { insumo_id: 1, nombre: 'Harina de maíz', unidad_medida: 'kg', cantidad: '50.00' },
]
const MARGENES: MargenProductoRead[] = [
  { producto_id: 1, variante_id: null, margen_total: '60000.00', margen_promedio: '5000.00' },
]
const RESUMEN = {
  desde: '2025-08-19',
  hasta: '2026-08-19',
  ventas_total: '150000.00',
  cantidad_ventas: 7,
  unidades_vendidas: '12.00',
  ticket_promedio: '21428.57',
  margen_total: '60000.00',
  gastos_total: '10000.00',
  resultado_neto: '50000.00',
  unidades_periodo_anterior: '10.00',
  ticket_periodo_anterior: '20000.00',
  ventas_periodo_anterior: '120000.00',
  margen_periodo_anterior: '50000.00',
  gastos_periodo_anterior: '9000.00',
  resultado_periodo_anterior: '41000.00',
}
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

async function mountView(): Promise<VueWrapper> {
  const wrapper = mount(AnalisisView, {
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('AnalisisView (ANA-4..6)', () => {
  it('renders the two direct tables with the joined product name and es-CO money/qty', async () => {
    apiMocks.topProductos.mockResolvedValue(TOP_PRODUCTOS)
    apiMocks.topInsumos.mockResolvedValue(TOP_INSUMOS)
    apiMocks.margenPorProducto.mockResolvedValue(MARGENES)
    apiMocks.finanzasMensuales.mockResolvedValue([])
    apiMocks.resumen.mockResolvedValue(RESUMEN)
    apiMocks.listProductos.mockResolvedValue({ items: PRODUCTOS, total: 1 })

    const wrapper = await mountView()

    const text = wrapper.text()
    expect(text).toContain('Productos más vendidos')
    expect(text).toContain('Arepa de huevo') // product name joined client-side
    expect(text).toContain('$150.000,00') // ingresos es-CO
    expect(text).toContain('Insumos más comprados')
    expect(text).toContain('Harina de maíz') // name comes inline from the API
    expect(text).toContain('kg')
    expect(text).toContain('50')
    expect(text).toContain('Rentabilidad por producto')
    expect(text).toContain('$60.000,00')
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 1000 })
  })

  it('degrades a missing product join to "Producto #id"', async () => {
    apiMocks.topProductos.mockResolvedValue([{ producto_id: 99, unidades: '1.00', ingresos: '8000.00' }])
    apiMocks.topInsumos.mockResolvedValue([])
    apiMocks.margenPorProducto.mockResolvedValue([])
    apiMocks.finanzasMensuales.mockResolvedValue([])
    apiMocks.resumen.mockResolvedValue(RESUMEN)
    apiMocks.listProductos.mockResolvedValue({ items: [], total: 0 })

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Producto #99')
  })

  it('renders the empty states when there is no data', async () => {
    apiMocks.topProductos.mockResolvedValue([])
    apiMocks.topInsumos.mockResolvedValue([])
    apiMocks.margenPorProducto.mockResolvedValue([])
    apiMocks.finanzasMensuales.mockResolvedValue([])
    apiMocks.resumen.mockResolvedValue(RESUMEN)
    apiMocks.listProductos.mockResolvedValue({ items: [], total: 0 })

    const wrapper = await mountView()

    const text = wrapper.text()
    expect(text).toContain('Sin ventas registradas')
    expect(text).toContain('Sin compras de insumos')
  })

  it('surfaces an error alert when the analytics load fails', async () => {
    apiMocks.topProductos.mockRejectedValue(new Error('network down'))

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('No se pudo cargar el análisis')
    // el-alert replaced by PrimeVue Message (slice 3a).
    expect(wrapper.find('.p-message').exists()).toBe(true)
  })
})
