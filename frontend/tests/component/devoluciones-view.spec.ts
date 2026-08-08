/**
 * DevolucionesView integration tests (task 2.3, spec MOD-2).
 *
 * Mounts the REAL DevolucionesView + DevolucionesTable + DevolucionesForm
 * against a mocked API module: the paginated /devoluciones list is joined
 * client-side (/productos?limit=1000), the filters drive the GET query, the
 * create section is role-gated (consulta = list only), and a submit routes
 * the payload through devolucionesApi.create, surfaces the success message
 * and refreshes the list.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'
import DevolucionesView from '@/views/DevolucionesView.vue'
import type { components } from '@/types/api.d'

type DevolucionRead = components['schemas']['DevolucionRead']

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listDevoluciones: vi.fn(),
    createDevolucion: vi.fn(),
    listProductos: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  devolucionesApi: { list: apiMocks.listDevoluciones, create: apiMocks.createDevolucion },
  productosApi: { list: apiMocks.listProductos },
}))

const DEVOLUCIONES: DevolucionRead[] = [
  {
    id: 3,
    venta_id: 10,
    fecha: '2026-08-02T14:00:00Z',
    motivo: 'Cliente devolvió dos arepas',
    monto_reembolsado: '10000.00',
    tipo: 'parcial',
    usuario_id: 2,
    items: [
      { id: 1, producto_id: 1, variante_id: null, cantidad: '2', precio_unitario: '5000.00', subtotal: '10000.00' },
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
]

const PAYLOAD = { venta_id: 10, tipo: 'parcial' as const, items: [{ producto_id: 1, cantidad: 2, precio_unitario: 5000 }] }

async function mountView(rol: string): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol },
  })
  const wrapper = mount(DevolucionesView, { global: { plugins: [pinia, ElementPlus] } })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('DevolucionesView (MOD-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMocks.listDevoluciones.mockResolvedValue(DEVOLUCIONES)
    apiMocks.listProductos.mockResolvedValue(PRODUCTOS)
    apiMocks.createDevolucion.mockResolvedValue(DEVOLUCIONES[0])
  })

  afterEach(() => {
    ElMessage.closeAll()
  })

  it('renders the joined list and the create section for an operador', async () => {
    const wrapper = await mountView('operador')

    const text = wrapper.text()
    expect(text).toContain('Parcial')
    expect(text).toContain('Cliente devolvió dos arepas')
    expect(text).toContain('$10.000,00')
    expect(text).toContain('Registrar devolución') // create section present for operador

    // List data joined client-side: productos fetched at limit 1000; the
    // paginated GET is called without filters on first load.
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listDevoluciones).toHaveBeenCalledWith({})

    // Expand the row -> the joined product name renders.
    await wrapper.find('.el-table__expand-icon').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Arepa de huevo')
  })

  it('hides the create section for a consulta (read-only list)', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.text()).toContain('Parcial')
    expect(wrapper.text()).not.toContain('Registrar devolución')
    expect(wrapper.findComponent({ name: 'DevolucionesForm' }).exists()).toBe(false)
  })

  it('shows an empty state when there are no devoluciones', async () => {
    apiMocks.listDevoluciones.mockResolvedValue([])

    const wrapper = await mountView('operador')

    expect(wrapper.text()).toContain('Sin devoluciones registradas')
  })

  it('surfaces an error alert when the list call fails', async () => {
    apiMocks.listDevoluciones.mockRejectedValue(new Error('network down'))

    const wrapper = await mountView('operador')

    expect(wrapper.text()).toContain('No se pudo cargar la lista de devoluciones')
  })

  it('posts the form payload, shows the success message and refreshes the list', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listDevoluciones).toHaveBeenCalledTimes(1)

    // The form emits its built DevolucionCreate payload (shape covered by
    // devoluciones-form.spec); the view owns the POST + refresh.
    wrapper.findComponent({ name: 'DevolucionesForm' }).vm.$emit('submit', PAYLOAD)
    await flushPromises()

    expect(apiMocks.createDevolucion).toHaveBeenCalledTimes(1)
    expect(apiMocks.createDevolucion).toHaveBeenCalledWith(PAYLOAD)
    expect(document.body.textContent).toContain('Devolución registrada correctamente')
    expect(apiMocks.listDevoluciones).toHaveBeenCalledTimes(2) // refreshed after create
  })

  it('applies the venta_id and fecha filters to the list query', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listDevoluciones).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-test="filtro-venta"] input').setValue('7')
    await wrapper.find('[data-test="apply-filters"]').trigger('click')
    await flushPromises()

    expect(apiMocks.listDevoluciones).toHaveBeenLastCalledWith({ venta_id: 7 })

    // Fecha range bound by the view's date pickers (value-format YYYY-MM-DD):
    // typing a value and blurring/change commits the picker model. Note:
    // el-date-picker swallows fallthrough data-test attrs, so we locate the
    // inner inputs by placeholder.
    const desde = wrapper.find('input[placeholder="Desde"]')
    await desde.setValue('2026-01-01')
    await desde.trigger('change')
    const hasta = wrapper.find('input[placeholder="Hasta"]')
    await hasta.setValue('2026-01-31')
    await hasta.trigger('change')
    await wrapper.find('[data-test="apply-filters"]').trigger('click')
    await flushPromises()

    expect(apiMocks.listDevoluciones).toHaveBeenLastCalledWith({
      venta_id: 7,
      fecha_desde: '2026-01-01',
      fecha_hasta: '2026-01-31',
    })

    // Limpiar resets the filters and reloads the unfiltered list.
    await wrapper.find('[data-test="clear-filters"]').trigger('click')
    await flushPromises()
    expect(apiMocks.listDevoluciones).toHaveBeenLastCalledWith({})
  })
})
