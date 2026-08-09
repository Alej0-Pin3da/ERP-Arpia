/**
 * VentasView integration tests (MOD-1 + ui-mantenimiento PR1 T7).
 *
 * Mounts the REAL VentasView + VentasTable + VentasForm against a mocked API
 * module: the /ventas list is now server-side paginated ({items,total} +
 * el-pagination + canal/estado filters replacing the old client-side slice),
 * still joined client-side (productos/variantes/clientes), the register tab is
 * role-gated (consulta = list only), and a submit routes the payload through
 * ventasApi.create, surfaces the success message and refreshes the list.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'
import VentasView from '@/views/VentasView.vue'
import type { components } from '@/types/api.d'

type VentaRead = components['schemas']['VentaRead']

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listVentas: vi.fn(),
    createVenta: vi.fn(),
    listProductos: vi.fn(),
    listVariantes: vi.fn(),
    listClientes: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  ventasApi: { list: apiMocks.listVentas, create: apiMocks.createVenta },
  productosApi: { list: apiMocks.listProductos, listVariantes: apiMocks.listVariantes },
  clientesApi: { list: apiMocks.listClientes },
}))

const VENTAS: VentaRead[] = [
  {
    id: 10,
    fecha: '2026-08-01T10:30:00Z',
    cliente_id: 7,
    canal_venta: 'whatsapp',
    descuento_porcentaje: '0',
    estado: 'completada',
    total_venta: '15000.00',
    detalles: [
      {
        id: 1,
        producto_id: 1,
        variante_id: null,
        cantidad: '2',
        precio_unitario_aplicado: '5000.00',
        costo_unitario_aplicado: '2000.00',
      },
      {
        id: 2,
        producto_id: 2,
        variante_id: null,
        cantidad: '1',
        precio_unitario_aplicado: '5000.00',
        costo_unitario_aplicado: '2000.00',
      },
    ],
  },
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
  {
    id: 2,
    tipo_producto_id: 1,
    nombre: 'Jugo de naranja',
    requiere_fabricacion: false,
    costos_operativos_fijos: '0',
    precio_venta_sugerido: '8000',
  },
]

const CLIENTES = [
  {
    id: 7,
    nombre: 'Juan Pérez',
    documento_identidad: null,
    email: null,
    telefono: null,
    created_at: '2026-01-01T00:00:00Z',
  },
]

const PAYLOAD = {
  cliente_id: null,
  canal_venta: 'web' as const,
  descuento_porcentaje: 0,
  detalles: [{ producto_id: 1, cantidad: 2, precio_unitario: 5000 }],
}

const PAGE1 = { limit: 20, offset: 0 }

async function mountView(rol: string): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol },
  })
  const wrapper = mount(VentasView, { global: { plugins: [pinia, ElementPlus] } })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('VentasView (MOD-1 + T7)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // The list now pages server-side; lookups keep limit:1000 with `.items`.
    apiMocks.listVentas.mockResolvedValue({ items: VENTAS, total: 1 })
    apiMocks.listProductos.mockResolvedValue({ items: PRODUCTOS, total: 2 })
    apiMocks.listClientes.mockResolvedValue({ items: CLIENTES, total: 1 })
    apiMocks.listVariantes.mockResolvedValue([])
    apiMocks.createVenta.mockResolvedValue(VENTAS[0])
  })

  afterEach(() => {
    ElMessage.closeAll()
  })

  it('renders the joined list and the register tab for an operador', async () => {
    const wrapper = await mountView('operador')

    const text = wrapper.text()
    expect(text).toContain('Arepa de huevo ×2')
    expect(text).toContain('Jugo de naranja ×1')
    expect(text).toContain('Juan Pérez')
    expect(text).toContain('$15.000,00')
    expect(text).toContain('Registrar venta') // form tab present for operador

    // List pages server-side; lookups join with limit:1000 against `.items`.
    expect(apiMocks.listVentas).toHaveBeenCalledWith(PAGE1)
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listClientes).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listVariantes).toHaveBeenCalledTimes(2)
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 1 })
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 2 })
  })

  it('renders el-pagination and pages the list with a new offset', async () => {
    const wrapper = await mountView('operador')
    expect(wrapper.findComponent({ name: 'ElPagination' }).exists()).toBe(true)
    expect(apiMocks.listVentas).toHaveBeenCalledWith(PAGE1)

    wrapper.findComponent({ name: 'ElPagination' }).vm.$emit('current-change', 2)
    await flushPromises()
    expect(apiMocks.listVentas).toHaveBeenCalledWith({ limit: 20, offset: 20 })
  })

  it('canal/estado filters reset to page 1 and refetch with the params', async () => {
    const wrapper = await mountView('operador')

    const select = wrapper.find('[data-test="venta-canal-filter"]')
    await select.trigger('click')
    await nextTick()
    const option = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
      (el) => el.textContent?.trim() === 'Feria',
    )
    expect(option).toBeDefined()
    option!.click()
    await flushPromises()

    expect(apiMocks.listVentas).toHaveBeenLastCalledWith({ ...PAGE1, canal_venta: 'feria' })
  })

  it('hides the register form for a consulta (read-only list)', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.text()).toContain('Arepa de huevo ×2')
    expect(wrapper.text()).not.toContain('Registrar venta')
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(false)
  })

  it('shows an empty state when there are no ventas', async () => {
    apiMocks.listVentas.mockResolvedValue({ items: [], total: 0 })

    const wrapper = await mountView('operador')

    expect(wrapper.text()).toContain('Sin ventas registradas')
  })

  it('surfaces an error alert when the list call fails', async () => {
    apiMocks.listVentas.mockRejectedValue(new Error('network down'))

    const wrapper = await mountView('operador')

    expect(wrapper.text()).toContain('No se pudo cargar la lista de ventas')
  })

  it('posts the form payload, shows the success message and refreshes the list', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1)

    wrapper.findComponent({ name: 'VentasForm' }).vm.$emit('submit', PAYLOAD)
    await flushPromises()

    expect(apiMocks.createVenta).toHaveBeenCalledTimes(1)
    expect(apiMocks.createVenta).toHaveBeenCalledWith(PAYLOAD)
    expect(document.body.textContent).toContain('Venta registrada correctamente')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(2) // refreshed after create
  })
})
