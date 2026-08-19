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
import Paginator from 'primevue/paginator'
import PrimeVue from 'primevue/config'
import Tooltip from 'primevue/tooltip'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import { useAuthStore } from '@/stores/auth'
import VentasView from '@/views/VentasView.vue'
import type { components } from '@/types/api.d'
import { clearToastHost, mountToastHost } from '../helpers/toast-host'

type VentaRead = components['schemas']['VentaRead']

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listVentas: vi.fn(),
    createVenta: vi.fn(),
    updateEsRegalo: vi.fn(),
    updateVenta: vi.fn(),
    anularVenta: vi.fn(),
    listProductos: vi.fn(),
    listVariantes: vi.fn(),
    listClientes: vi.fn(),
  },
}))
const confirmMocks = vi.hoisted(() => ({ confirmAction: vi.fn() }))
vi.mock('@/utils/confirm', () => ({ confirmAction: confirmMocks.confirmAction }))
vi.mock('@/api/endpoints', () => ({
  ventasApi: {
    list: apiMocks.listVentas,
    create: apiMocks.createVenta,
    updateEsRegalo: apiMocks.updateEsRegalo,
    update: apiMocks.updateVenta,
    anular: apiMocks.anularVenta,
  },
  productosApi: { list: apiMocks.listProductos, listVariantes: apiMocks.listVariantes },
  clientesApi: { list: apiMocks.listClientes },
}))

// Fake PrimeVue Toast host: renders showToast() messages into <body> so the
// existing `document.body.textContent` assertions keep working.
mountToastHost()

const VENTAS: VentaRead[] = [
  {
    id: 10,
    fecha: '2026-08-01T10:30:00Z',
    cliente_id: 7,
    canal_venta: 'whatsapp',
    descuento_porcentaje: '0',
    estado: 'completada',
    es_regalo: false,
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
  es_regalo: false,
  detalles: [{ producto_id: 1, cantidad: 2, precio_unitario: 5000 }],
}

const PAGE1 = { limit: 20, offset: 0 }

/** Let the dialog leave transition finish (Vue's nextFrame is a double rAF). */
async function flushDialogTransition(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

/** Let a PrimeVue Select overlay open (Teleport + transition) before interacting. */
async function flushOverlay(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

/** Open a PrimeVue Select by its data-test and click the option with the label. */
async function pickOption(select: ReturnType<VueWrapper['find']>, label: string): Promise<void> {
  await select.trigger('click')
  await flushOverlay()
  const item = [...document.querySelectorAll<HTMLElement>('.p-select-option')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`dropdown option not found: "${label}"`)
  item.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
  await flushOverlay()
  await nextTick()
}

async function mountView(rol: string): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol },
  })
  const wrapper = mount(VentasView, {
    global: {
      plugins: [
        pinia,
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
      directives: { tooltip: Tooltip },
      stubs: { transition: false },
    },
  })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('VentasView (MOD-1 + T7)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    confirmMocks.confirmAction.mockReset()
    // The list now pages server-side; lookups keep limit:1000 with `.items`.
    apiMocks.listVentas.mockResolvedValue({ items: VENTAS, total: 1 })
    apiMocks.listProductos.mockResolvedValue({ items: PRODUCTOS, total: 2 })
    apiMocks.listClientes.mockResolvedValue({ items: CLIENTES, total: 1 })
    apiMocks.listVariantes.mockResolvedValue([])
    apiMocks.createVenta.mockResolvedValue(VENTAS[0])
    apiMocks.updateEsRegalo.mockResolvedValue({ ...VENTAS[0], es_regalo: true })
    apiMocks.updateVenta.mockResolvedValue(VENTAS[0])
    apiMocks.anularVenta.mockResolvedValue({ ...VENTAS[0], estado: 'anulada' })
  })

  afterEach(() => {
    clearToastHost()
  })

  it('renders the joined list and the register button for an operador', async () => {
    const wrapper = await mountView('operador')

    const text = wrapper.text()
    expect(text).toContain('Arepa de huevo ×2')
    expect(text).toContain('Jugo de naranja ×1')
    expect(text).toContain('Juan Pérez')
    expect(text).toContain('$15.000,00')
    expect(wrapper.find('[data-test="nueva-venta"]').exists()).toBe(true) // register button for operador

    // List pages server-side; lookups join with limit:1000 against `.items`.
    expect(apiMocks.listVentas).toHaveBeenCalledWith(PAGE1)
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listClientes).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listVariantes).toHaveBeenCalledTimes(2)
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 1 })
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 2 })
  })

  it('renders Paginator and pages the list with a new offset', async () => {
    const wrapper = await mountView('operador')
    expect(wrapper.findComponent(Paginator).exists()).toBe(true)
    expect(apiMocks.listVentas).toHaveBeenCalledWith(PAGE1)

    wrapper.findComponent(Paginator).vm.$emit('page', { first: 20, rows: 20 })
    await flushPromises()
    expect(apiMocks.listVentas).toHaveBeenCalledWith({ limit: 20, offset: 20 })
  })

  it('canal/estado filters reset to page 1 and refetch with the params', async () => {
    const wrapper = await mountView('operador')

    await pickOption(wrapper.find('[data-test="venta-canal-filter"]'), 'Feria')
    expect(apiMocks.listVentas).toHaveBeenLastCalledWith({ ...PAGE1, canal_venta: 'feria' })
  })

  it('product filter sends producto_id and resets to page 1', async () => {
    const wrapper = await mountView('operador')

    await pickOption(wrapper.find('[data-test="venta-producto-filter"]'), 'Jugo de naranja')
    expect(apiMocks.listVentas).toHaveBeenLastCalledWith({ ...PAGE1, producto_id: 2 })
  })

  it('wires the header column filters into the same server-side filter refs', async () => {
    const wrapper = await mountView('operador')

    const table = wrapper.findComponent({ name: 'VentasTable' })
    table.vm.$emit('filter-change', { canal_venta: 'feria', estado: 'anulada' })
    await flushPromises()

    expect(apiMocks.listVentas).toHaveBeenLastCalledWith({ ...PAGE1, canal_venta: 'feria', estado: 'anulada' })
  })

  it('wires the header column sort into server-side sort params and resets the page', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1)

    wrapper
      .findComponent({ name: 'VentasTable' })
      .vm.$emit('sort-change', { prop: 'total_venta', order: 'desc' })
    await flushPromises()

    expect(apiMocks.listVentas).toHaveBeenCalledTimes(2)
    expect(apiMocks.listVentas).toHaveBeenLastCalledWith({ ...PAGE1, sort_by: 'total_venta', order: 'desc' })
  })

  it('clears the server-side sort when the column order is null', async () => {
    const wrapper = await mountView('operador')

    wrapper
      .findComponent({ name: 'VentasTable' })
      .vm.$emit('sort-change', { prop: 'total_venta', order: 'desc' })
    await flushPromises()
    expect(apiMocks.listVentas).toHaveBeenLastCalledWith({ ...PAGE1, sort_by: 'total_venta', order: 'desc' })

    wrapper.findComponent({ name: 'VentasTable' }).vm.$emit('sort-change', { prop: 'total_venta', order: null })
    await flushPromises()
    expect(apiMocks.listVentas).toHaveBeenLastCalledWith(PAGE1)
  })

  it('hides the register button for a consulta (read-only list)', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.text()).toContain('Arepa de huevo ×2')
    expect(wrapper.find('[data-test="nueva-venta"]').exists()).toBe(false)
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
    // el-alert replaced by PrimeVue Message (slice 3a).
    expect(wrapper.find('.p-message').exists()).toBe(true)
  })

  it('opens the dialog, posts the form payload, shows the success message, closes and refreshes the list', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1)

    // The form lives in a PrimeVue Dialog opened from the toolbar button (FE-DLG-1).
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(false)
    await wrapper.find('[data-test="nueva-venta"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'VentasForm' }).vm.$emit('submit', PAYLOAD)
    await flushPromises()

    expect(apiMocks.createVenta).toHaveBeenCalledTimes(1)
    expect(apiMocks.createVenta).toHaveBeenCalledWith(PAYLOAD)
    expect(document.body.textContent).toContain('Venta registrada correctamente')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(2) // refreshed after create
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(false)
  })

  it('cancels the register dialog without submitting (FE-DLG-2/3)', async () => {
    const wrapper = await mountView('operador')

    await wrapper.find('[data-test="nueva-venta"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(true)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape' }))
    await flushDialogTransition()

    expect(apiMocks.createVenta).not.toHaveBeenCalled()
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(false)
  })

  it('keeps the dialog open and shows the error when the save fails (FE-DLG-2)', async () => {
    apiMocks.createVenta.mockRejectedValue({ response: { data: { detail: 'Stock insuficiente' } } })
    const wrapper = await mountView('operador')

    await wrapper.find('[data-test="nueva-venta"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'VentasForm' }).vm.$emit('submit', PAYLOAD)
    await flushPromises()

    expect(document.body.textContent).toContain('Stock insuficiente')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1) // no refresh on failure
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(true)
  })

  it('marks a venta as regalo after confirming (PATCH + refresh)', async () => {
    confirmMocks.confirmAction.mockResolvedValue('accept')
    const wrapper = await mountView('operador')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-test="marcar-regalo"]').trigger('click')
    await flushPromises()

    expect(confirmMocks.confirmAction).toHaveBeenCalled()
    expect(apiMocks.updateEsRegalo).toHaveBeenCalledWith({ venta_id: 10 }, { es_regalo: true })
    expect(document.body.textContent).toContain('Venta marcada como regalo')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(2) // refreshed after PATCH
  })

  it('does not PATCH when the user cancels the confirmation', async () => {
    confirmMocks.confirmAction.mockResolvedValue('reject')
    const wrapper = await mountView('operador')

    await wrapper.find('[data-test="marcar-regalo"]').trigger('click')
    await flushPromises()

    expect(apiMocks.updateEsRegalo).not.toHaveBeenCalled()
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1) // no refresh
  })

  it('hides the marcar-regalo action for a consulta (read-only list)', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.find('[data-test="marcar-regalo"]').exists()).toBe(false)
  })

  it('edits a venta: Editar opens the dialog in edit mode, PUTs the payload, closes and refreshes', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-test="editar-venta"]').trigger('click')
    await nextTick()
    await flushPromises()

    const form = wrapper.findComponent({ name: 'VentasForm' })
    expect(form.exists()).toBe(true)
    expect(form.props('mode')).toBe('edit')
    expect((form.props('initial') as VentaRead).id).toBe(10)

    form.vm.$emit('submit', PAYLOAD)
    await flushPromises()

    expect(apiMocks.updateVenta).toHaveBeenCalledTimes(1)
    expect(apiMocks.updateVenta).toHaveBeenCalledWith({ venta_id: 10 }, PAYLOAD)
    expect(document.body.textContent).toContain('Venta actualizada correctamente')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(2) // refreshed after PUT
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(false)
  })

  it('keeps the dialog open and shows the error when the edit save fails', async () => {
    apiMocks.updateVenta.mockRejectedValue({ response: { data: { detail: 'Stock insuficiente' } } })
    const wrapper = await mountView('operador')

    await wrapper.find('[data-test="editar-venta"]').trigger('click')
    await nextTick()
    await flushPromises()

    wrapper.findComponent({ name: 'VentasForm' }).vm.$emit('submit', PAYLOAD)
    await flushPromises()

    expect(document.body.textContent).toContain('Stock insuficiente')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1) // no refresh on failure
    expect(wrapper.findComponent({ name: 'VentasForm' }).exists()).toBe(true)
  })

  it('anula a venta after confirming (DELETE + refresh)', async () => {
    confirmMocks.confirmAction.mockResolvedValue('accept')
    const wrapper = await mountView('operador')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-test="anular-venta"]').trigger('click')
    await flushPromises()

    expect(apiMocks.anularVenta).toHaveBeenCalledWith({ venta_id: 10 })
    expect(document.body.textContent).toContain('Venta anulada correctamente')
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(2) // refreshed after DELETE
  })

  it('does not DELETE when the anular confirmation is cancelled', async () => {
    confirmMocks.confirmAction.mockResolvedValue('reject')
    const wrapper = await mountView('operador')

    await wrapper.find('[data-test="anular-venta"]').trigger('click')
    await flushPromises()

    expect(apiMocks.anularVenta).not.toHaveBeenCalled()
    expect(apiMocks.listVentas).toHaveBeenCalledTimes(1) // no refresh
  })
})
