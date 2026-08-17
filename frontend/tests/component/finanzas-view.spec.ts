/**
 * FinanzasView integration tests (PR8, spec MOD-3).
 *
 * Mounts the REAL FinanzasView + all finanzas components against a mocked
 * finanzasApi: the three tabs (Movimientos / Liquidaciones / Socios), the
 * client-side socio join, role visibility (consulta = read-only lists, no
 * Liquidaciones tab, no write actions), movimiento create + soft-delete
 * (confirm dialog -> DELETE expects 200 -> refresh; cancel -> nothing), the
 * liquidacion settlement result table + 409 replay surfacing, and the socios
 * create/edit/delete flows (PATCH percentage only; delete 409 surfaced).
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage, ElMessageBox } from 'element-plus'
import Paginator from 'primevue/paginator'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import { useAuthStore } from '@/stores/auth'
import FinanzasView from '@/views/FinanzasView.vue'
import type { components } from '@/types/api.d'

type MovimientoRead = components['schemas']['MovimientoRead']
type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listMovimientos: vi.fn(),
    createMovimiento: vi.fn(),
    updateMovimiento: vi.fn(),
    deleteMovimiento: vi.fn(),
    listSocios: vi.fn(),
    createSocio: vi.fn(),
    updateSocio: vi.fn(),
    deleteSocio: vi.fn(),
    createLiquidacion: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  finanzasApi: {
    listMovimientos: apiMocks.listMovimientos,
    createMovimiento: apiMocks.createMovimiento,
    updateMovimiento: apiMocks.updateMovimiento,
    deleteMovimiento: apiMocks.deleteMovimiento,
    listSocios: apiMocks.listSocios,
    createSocio: apiMocks.createSocio,
    updateSocio: apiMocks.updateSocio,
    deleteSocio: apiMocks.deleteSocio,
    createLiquidacion: apiMocks.createLiquidacion,
  },
}))

const MOVIMIENTOS: MovimientoRead[] = [
  {
    id: 1,
    fecha: '2026-08-01T10:00:00Z',
    tipo: 'Gasto',
    descripcion: 'Compra de arepas',
    monto: '50000.00',
    socio_id: null,
    estado: 'activo',
    liquidacion_id: null,
  },
  {
    id: 2,
    fecha: '2026-08-02T12:00:00Z',
    tipo: 'Retiro',
    descripcion: 'Retiro a socio',
    monto: '150000.00',
    socio_id: 1,
    estado: 'activo',
    liquidacion_id: null,
  },
]

const SOCIOS: SocioConfiguracionRead[] = [
  { id: 1, nombre: 'Ana María', porcentaje_participacion: '60.00' },
  { id: 2, nombre: 'Carlos Ruiz', porcentaje_participacion: '40.00' },
]

const LIQUIDACION_RESULT: MovimientoRead[] = [
  { id: 3, fecha: '2026-08-05T09:00:00Z', tipo: 'Retiro', descripcion: 'Liquidación xyz', monto: '3000000.00', socio_id: 1, estado: 'activo', liquidacion_id: 'xyz00' },
  { id: 4, fecha: '2026-08-05T09:00:00Z', tipo: 'Retiro', descripcion: 'Liquidación xyz', monto: '2000000.00', socio_id: 2, estado: 'activo', liquidacion_id: 'xyz01' },
]

async function mountView(rol: string): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol },
  })
  const wrapper = mount(FinanzasView, {
    global: {
      plugins: [
        pinia,
        ElementPlus,
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
      stubs: { transition: false },
    },
  })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

/** Click the PrimeVue Tab with the given label (panels stay mounted via v-show). */
async function activateTab(wrapper: VueWrapper, label: string): Promise<void> {
  const item = wrapper.findAll('.p-tab').find((i) => i.text().trim() === label)
  if (!item) throw new Error(`tab not found: "${label}"`)
  await item.trigger('click')
  await nextTick()
  await flushPromises()
}

/** Let the el-dialog leave transition finish (Vue's nextFrame is a double rAF). */
async function flushDialogTransition(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

describe('FinanzasView (MOD-3 + T7)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Lists page server-side; the socios lookup keeps limit:1000 (D3).
    apiMocks.listMovimientos.mockResolvedValue({ items: MOVIMIENTOS, total: 2 })
    apiMocks.listSocios.mockResolvedValue({ items: SOCIOS, total: 2 })
    apiMocks.createMovimiento.mockResolvedValue(MOVIMIENTOS[0])
    apiMocks.updateMovimiento.mockResolvedValue(MOVIMIENTOS[0])
    apiMocks.deleteMovimiento.mockResolvedValue(MOVIMIENTOS[0])
    apiMocks.createSocio.mockResolvedValue({ id: 3, nombre: 'Luis Vega', porcentaje_participacion: '25.00' })
    apiMocks.updateSocio.mockResolvedValue({ id: 1, nombre: 'Ana María', porcentaje_participacion: '20.00' })
    apiMocks.deleteSocio.mockResolvedValue(undefined)
    apiMocks.createLiquidacion.mockResolvedValue(LIQUIDACION_RESULT)
  })

  afterEach(() => {
    ElMessage.closeAll()
    vi.restoreAllMocks()
  })

  it('renders the three tabs, the joined movimientos list and the create buttons for an operador', async () => {
    const wrapper = await mountView('operador')

    const text = wrapper.text()
    expect(text).toContain('Movimientos')
    expect(text).toContain('Liquidaciones')
    expect(text).toContain('Socios')

    // Joined list: socio name rendered, monto es-CO, newest first.
    expect(text).toContain('Ana María')
    expect(text).toContain('Retiro a socio')
    expect(text).toContain('$150.000,00')
    expect(text).toContain('$50.000,00')

    // Both lists fetched on mount (socios drive the join + the socio select).
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1)
    expect(apiMocks.listMovimientos).toHaveBeenCalledWith({ limit: 20, offset: 0 })
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(2) // table page + lookup
    expect(apiMocks.listSocios).toHaveBeenCalledWith({ limit: 20, offset: 0 })
    expect(apiMocks.listSocios).toHaveBeenCalledWith({ limit: 1000 })

    // Write buttons present for operador; the forms live in el-dialogs (FE-DLG-1).
    expect(wrapper.find('[data-test="nuevo-movimiento"]').exists()).toBe(true)
    await activateTab(wrapper, 'Liquidaciones')
    expect(wrapper.text()).toContain('Procesar liquidación')
    await activateTab(wrapper, 'Socios')
    expect(wrapper.find('[data-test="nuevo-socio"]').exists()).toBe(true)
  })

  it('renders Paginator on both lists and pages with new offsets', async () => {
    const wrapper = await mountView('operador')
    // Movimientos table paginator (first Paginator in the pane).
    const paginators = wrapper.findAllComponents(Paginator)
    expect(paginators.length).toBeGreaterThanOrEqual(1)
    expect(apiMocks.listMovimientos).toHaveBeenCalledWith({ limit: 20, offset: 0 })

    // Two paginators exist (movimientos + socios); drive the movimientos one.
    const movPaginador = paginators.find((p) => p.props('totalRecords') === 2)
    expect(movPaginador).toBeDefined()
    movPaginador!.vm.$emit('page', { first: 20, rows: 20 })
    await flushPromises()
    expect(apiMocks.listMovimientos).toHaveBeenCalledWith({ limit: 20, offset: 20 })
  })

  it('filters movimientos by tipo with page reset', async () => {
    const wrapper = await mountView('operador')

    const select = wrapper.find('[data-test="movimiento-tipo-filter"]')
    await select.trigger('click')
    await nextTick()
    const option = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
      (el) => el.textContent?.trim() === 'Gasto',
    )
    expect(option).toBeDefined()
    option!.click()
    await flushPromises()

    expect(apiMocks.listMovimientos).toHaveBeenLastCalledWith({
      limit: 20,
      offset: 0,
      tipo: 'Gasto',
    })
  })

  it('wires the header column filter on the movimientos table into the tipo ref', async () => {
    const wrapper = await mountView('operador')

    const table = wrapper.findComponent({ name: 'MovimientosTable' })
    table.vm.$emit('filter-change', { tipo: 'Retiro' })
    await flushPromises()

    expect(apiMocks.listMovimientos).toHaveBeenLastCalledWith({
      limit: 20,
      offset: 0,
      tipo: 'Retiro',
    })
  })

  it('wires the movimientos table sort-change into server-side sort params', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1)

    wrapper.findComponent({ name: 'MovimientosTable' }).vm.$emit('sort-change', { prop: 'monto', order: 'desc' })
    await flushPromises()

    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(2)
    expect(apiMocks.listMovimientos).toHaveBeenLastCalledWith({
      limit: 20,
      offset: 0,
      sort_by: 'monto',
      order: 'desc',
    })
  })

  it('wires the socios table sort-change into server-side sort params', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Socios')
    expect(apiMocks.listSocios).toHaveBeenCalledWith({ limit: 20, offset: 0 })

    wrapper.findComponent({ name: 'SociosTable' }).vm.$emit('sort-change', { prop: 'nombre', order: 'asc' })
    await flushPromises()

    // socios is fetched twice per load: the table page (with sort) + the lookup.
    expect(apiMocks.listSocios).toHaveBeenCalledWith({ limit: 20, offset: 0 })
    expect(apiMocks.listSocios).toHaveBeenCalledWith({
      limit: 20,
      offset: 0,
      sort_by: 'nombre',
      order: 'asc',
    })
    expect(apiMocks.listSocios).toHaveBeenCalledWith({ limit: 1000 })
  })

  it('consulta sees read-only lists only — no write actions, no Liquidaciones tab', async () => {
    const wrapper = await mountView('consulta')

    const text = wrapper.text()
    expect(text).toContain('Ana María')
    expect(wrapper.find('[data-test="nuevo-movimiento"]').exists()).toBe(false)
    expect(text).not.toContain('Procesar liquidación')
    expect(wrapper.find('[data-test="nuevo-socio"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-test="delete-movimiento"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="edit-socio"]')).toHaveLength(0)

    // The Liquidaciones tab is hidden entirely for read-only roles.
    await activateTab(wrapper, 'Socios')
    expect(wrapper.findComponent({ name: 'SociosForm' }).exists()).toBe(false)
  })

  it('opens the dialog, creates a movimiento, shows the success message, closes and refreshes the list', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1)

    // The form lives in an el-dialog opened from the toolbar button (FE-DLG-1).
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(false)
    await wrapper.find('[data-test="nuevo-movimiento"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'MovimientosForm' }).vm.$emit('submit', {
      tipo: 'Gasto',
      descripcion: 'Compra de arepas',
      monto: 50000,
    })
    await flushPromises()

    expect(apiMocks.createMovimiento).toHaveBeenCalledTimes(1)
    expect(apiMocks.createMovimiento).toHaveBeenCalledWith({ tipo: 'Gasto', descripcion: 'Compra de arepas', monto: 50000 })
    expect(document.body.textContent).toContain('Movimiento registrado correctamente')
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(2) // refreshed after create
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(false)
  })

  it('cancels the movimiento dialog without submitting (FE-DLG-2/3)', async () => {
    const wrapper = await mountView('operador')

    await wrapper.find('[data-test="nuevo-movimiento"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(true)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushDialogTransition()

    expect(apiMocks.createMovimiento).not.toHaveBeenCalled()
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(false)
  })

  it('soft-deletes a movimiento after the confirm dialog (DELETE expects 200)', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    const wrapper = await mountView('operador')
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1)

    const buttons = wrapper.findAll('[data-test="delete-movimiento"]')
    expect(buttons).toHaveLength(2)
    await buttons[0].trigger('click') // newest first -> id 2
    await flushPromises()

    expect(apiMocks.deleteMovimiento).toHaveBeenCalledTimes(1)
    expect(apiMocks.deleteMovimiento).toHaveBeenCalledWith({ movimiento_id: 2 })
    expect(document.body.textContent).toContain('Movimiento eliminado correctamente')
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(2) // refreshed after delete
  })

  it('does not call the API when the delete confirm dialog is cancelled', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockRejectedValue('cancel' as never)
    const wrapper = await mountView('operador')

    await wrapper.findAll('[data-test="delete-movimiento"]')[0].trigger('click')
    await flushPromises()

    expect(apiMocks.deleteMovimiento).not.toHaveBeenCalled()
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1)
  })

  it('processes a liquidacion and shows the per-socio result table', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Liquidaciones')

    wrapper.findComponent({ name: 'LiquidacionesForm' }).vm.$emit('submit', { monto: 5000000 })
    await flushPromises()

    expect(apiMocks.createLiquidacion).toHaveBeenCalledTimes(1)
    expect(apiMocks.createLiquidacion).toHaveBeenCalledWith({ monto: 5000000 })
    expect(document.body.textContent).toContain('Liquidación procesada correctamente')

    // Per-socio shares joined with partner names: 60% -> $3.000.000,00.
    expect(wrapper.text()).toContain('Resultado de la liquidación')
    expect(wrapper.text()).toContain('Ana María')
    expect(wrapper.text()).toContain('$3.000.000,00')
    expect(wrapper.text()).toContain('Carlos Ruiz')
    expect(wrapper.text()).toContain('$2.000.000,00')

    // The settlement created Retiro rows — the movimientos list refreshes too.
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(2)
  })

  it('surfaces the 409 replay error and shows no result table', async () => {
    apiMocks.createLiquidacion.mockRejectedValue({
      response: { data: { detail: 'La liquidación abc ya fue procesada' } },
    })
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Liquidaciones')

    wrapper.findComponent({ name: 'LiquidacionesForm' }).vm.$emit('submit', { monto: 5000000 })
    await flushPromises()

    expect(document.body.textContent).toContain('ya fue procesada')
    expect(wrapper.text()).not.toContain('Resultado de la liquidación')
  })

  it('opens the socio dialog, creates a socio and refreshes the list', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Socios')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(2) // table page + lookup

    await wrapper.find('[data-test="nuevo-socio"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'SociosForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'SociosForm' }).vm.$emit('submit', {
      nombre: 'Luis Vega',
      porcentaje_participacion: 25,
    })
    await flushPromises()

    expect(apiMocks.createSocio).toHaveBeenCalledTimes(1)
    expect(apiMocks.createSocio).toHaveBeenCalledWith({ nombre: 'Luis Vega', porcentaje_participacion: 25 })
    expect(document.body.textContent).toContain('Socio creado correctamente')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(4) // refreshed after create (2 per load)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'SociosForm' }).exists()).toBe(false)
  })

  it('edits a socio percentage via the edit dialog (PATCH percentage only) and closes it on success', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Socios')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(2) // table page + lookup

    await wrapper.findAll('[data-test="edit-socio"]')[0].trigger('click')
    await nextTick()

    // The edit form lives in the dialog; the name is read-only in edit mode.
    expect(wrapper.text()).toContain('Editar socio')
    expect(wrapper.findComponent({ name: 'SociosForm' }).exists()).toBe(true)
    expect(wrapper.find('[data-test="nombre-socio-input"]').exists()).toBe(false)

    wrapper.findComponent({ name: 'SociosForm' }).vm.$emit('submit', { porcentaje_participacion: 20 })
    await flushPromises()

    expect(apiMocks.updateSocio).toHaveBeenCalledTimes(1)
    expect(apiMocks.updateSocio).toHaveBeenCalledWith({ socio_id: 1 }, { porcentaje_participacion: 20 })
    expect(document.body.textContent).toContain('Socio actualizado correctamente')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(4) // table + lookup, refreshed

    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'SociosForm' }).exists()).toBe(false)
  })

  it('deletes a socio after the confirm dialog and refreshes', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Socios')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(2) // table page + lookup

    await wrapper.findAll('[data-test="delete-socio"]')[0].trigger('click')
    await flushPromises()

    expect(apiMocks.deleteSocio).toHaveBeenCalledTimes(1)
    expect(apiMocks.deleteSocio).toHaveBeenCalledWith({ socio_id: 1 })
    expect(document.body.textContent).toContain('Socio eliminado correctamente')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(4) // table + lookup, refreshed
  })

  it('surfaces the 409 when deleting a socio with payouts', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    apiMocks.deleteSocio.mockRejectedValue({
      response: { data: { detail: 'El socio tiene movimientos asociados; no se puede eliminar' } },
    })
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Socios')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(2) // table page + lookup

    await wrapper.findAll('[data-test="delete-socio"]')[0].trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('tiene movimientos asociados')
    expect(apiMocks.listSocios).toHaveBeenCalledTimes(2) // no refresh after failure
  })

  it('opens the movimiento edit dialog with prefill, PATCHes on submit, closes and refreshes (T9)', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1)

    await wrapper.findAll('[data-test="edit-movimiento"]')[0].trigger('click')
    await nextTick()

    // The edit form lives in the dialog with the create form replaced (T9 -> dialog).
    expect(wrapper.text()).toContain('Editar movimiento')
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'MovimientosForm' }).vm.$emit('submit', {
      fecha: '2026-08-02T12:00:00',
      tipo: 'Retiro',
      descripcion: 'Retiro a socio',
      monto: 150000,
      socio_id: 1,
    })
    await flushPromises()

    expect(apiMocks.updateMovimiento).toHaveBeenCalledTimes(1)
    expect(apiMocks.updateMovimiento).toHaveBeenCalledWith(
      { movimiento_id: 2 },
      {
        fecha: '2026-08-02T12:00:00',
        tipo: 'Retiro',
        descripcion: 'Retiro a socio',
        monto: 150000,
        socio_id: 1,
      },
    )
    expect(document.body.textContent).toContain('Movimiento actualizado correctamente')
    // Success closes the dialog and refreshes the list (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(false)
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(2)
  })

  it('keeps the edit dialog open and shows the server detail when the PATCH fails (T9)', async () => {
    apiMocks.updateMovimiento.mockRejectedValue({
      response: {
        data: { detail: 'Los movimientos de una liquidación no permiten cambiar monto ni socio' },
      },
    })
    const wrapper = await mountView('operador')
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1)

    await wrapper.findAll('[data-test="edit-movimiento"]')[0].trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('Editar movimiento')
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'MovimientosForm' }).vm.$emit('submit', {
      tipo: 'Retiro',
      descripcion: 'Retiro a socio',
      monto: 150000,
    })
    await flushPromises()

    // Error surfaces the 422 detail and does NOT close the dialog.
    expect(document.body.textContent).toContain('no permiten cambiar monto ni socio')
    expect(wrapper.findComponent({ name: 'MovimientosForm' }).exists()).toBe(true)
    expect(apiMocks.listMovimientos).toHaveBeenCalledTimes(1) // no refresh on failure
  })

  it('consulta sees no edit action on the movimientos table (T9)', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.findAll('[data-test="edit-movimiento"]')).toHaveLength(0)
  })
})

