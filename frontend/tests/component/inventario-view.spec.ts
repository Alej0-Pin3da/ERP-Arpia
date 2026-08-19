/**
 * InventarioView integration tests (PR9 MOD-4 + ui-mantenimiento PR1 T6).
 *
 * Mounts the REAL InventarioView + all inventario components against mocked
 * insumosApi/comprasApi/categoriasInsumosApi: the two tabs (Insumos /
 * Compras), server-side pagination ({items,total} + el-pagination driving
 * limit/offset refetches), toolbar filters (q + categoria_id insumos,
 * insumo_id compras) that reset to page 1, the server-joined insumos list,
 * below-minimum row highlighting, role visibility, the compras register flow
 * and the admin insumo create/edit/delete flows. Lookup joins keep limit:1000
 * against `.items` (design D3).
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import Paginator from 'primevue/paginator'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import { useAuthStore } from '@/stores/auth'
import InventarioView from '@/views/InventarioView.vue'
import type { components } from '@/types/api.d'
import { clearToastHost, mountToastHost } from '../helpers/toast-host'

type InsumoRead = components['schemas']['InsumoRead']
type CompraInsumoRead = components['schemas']['CompraInsumoRead']
type CategoriaInsumoRead = components['schemas']['CategoriaInsumoRead']

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listInsumos: vi.fn(),
    createInsumo: vi.fn(),
    updateInsumo: vi.fn(),
    deleteInsumo: vi.fn(),
    listCompras: vi.fn(),
    createCompra: vi.fn(),
    listCategorias: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  insumosApi: {
    list: apiMocks.listInsumos,
    create: apiMocks.createInsumo,
    update: apiMocks.updateInsumo,
    delete: apiMocks.deleteInsumo,
  },
  comprasApi: {
    list: apiMocks.listCompras,
    create: apiMocks.createCompra,
  },
  categoriasInsumosApi: {
    list: apiMocks.listCategorias,
  },
}))
const confirmMocks = vi.hoisted(() => ({ confirmAction: vi.fn() }))
vi.mock('@/utils/confirm', () => ({ confirmAction: confirmMocks.confirmAction }))

// Fake PrimeVue Toast host: renders showToast() messages into <body>.
mountToastHost()

const INSUMOS: InsumoRead[] = [
  {
    id: 1,
    categoria_id: 1,
    nombre: 'Harina de maíz',
    unidad_medida: 'kg',
    stock_actual: '12.00',
    stock_minimo: '5.00',
    costo_promedio_actual: '2500.00',
    nombre_categoria: 'Granos', // server-side join, rendered as-is
  },
  {
    id: 2,
    categoria_id: 2,
    nombre: 'Aceite',
    unidad_medida: 'L',
    stock_actual: '2.00', // below half the minimum -> Crítico
    stock_minimo: '10.00',
    costo_promedio_actual: '9800.00',
    nombre_categoria: 'Abarrotes',
  },
  {
    id: 3,
    categoria_id: 1,
    nombre: 'Sal',
    unidad_medida: 'kg',
    stock_actual: '8.00',
    stock_minimo: '3.00',
    costo_promedio_actual: '800.00',
    nombre_categoria: null,
  },
]

const COMPRAS: CompraInsumoRead[] = [
  {
    id: 1,
    insumo_id: 1,
    fecha_compra: '2026-08-01T09:00:00Z',
    cantidad_comprada: '3.00',
    precio_unitario_compra: '2500.00',
  },
]

const CATEGORIAS: CategoriaInsumoRead[] = [
  { id: 1, nombre: 'Granos' },
  { id: 2, nombre: 'Abarrotes' },
]

/** Page default for the table fetch (page 1, pageSize 20). */
const PAGE1 = { limit: 20, offset: 0 }

async function mountView(rol: string): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 2, nombre: 'Pepe', email: 'pepe@arpia.com.co', rol },
  })
  const wrapper = mount(InventarioView, {
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

describe('InventarioView (MOD-4 + T6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    confirmMocks.confirmAction.mockReset()
    // Table fetches use the page contract; lookups keep limit:1000 with `.items`.
    apiMocks.listInsumos.mockResolvedValue({ items: INSUMOS, total: 3 })
    apiMocks.listCompras.mockResolvedValue({ items: COMPRAS, total: 1 })
    apiMocks.listCategorias.mockResolvedValue({ items: CATEGORIAS, total: 2 })
    apiMocks.createInsumo.mockResolvedValue(INSUMOS[0])
    apiMocks.updateInsumo.mockResolvedValue({ ...INSUMOS[0], nombre: 'Harina premium' })
    apiMocks.deleteInsumo.mockResolvedValue(undefined)
    apiMocks.createCompra.mockResolvedValue(COMPRAS[0])
  })

  afterEach(() => {
    clearToastHost()
    vi.restoreAllMocks()
  })

  it('renders the two tabs and the server-joined insumos list for an operador', async () => {
    const wrapper = await mountView('operador')

    const text = wrapper.text()
    expect(text).toContain('Insumos')
    expect(text).toContain('Compras')

    expect(text).toContain('Harina de maíz')
    expect(text).toContain('Granos')
    expect(text).toContain('Sal')
    expect(text).toContain('—')
    expect(text).toContain('$2.500,00') // costo_promedio_actual es-CO

    // Table fetch pages; the lookup join keeps limit:1000.
    expect(apiMocks.listInsumos).toHaveBeenCalledWith(PAGE1)
    expect(apiMocks.listInsumos).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listCompras).toHaveBeenCalledWith(PAGE1)
  })

  it('renders Paginator with the server total on both tabs', async () => {
    const wrapper = await mountView('operador')
    // Both lists page via PrimeVue Paginator; the totals come from the API
    // (3 insumos, 1 compra), not a local guess.
    const paginators = wrapper.findAllComponents(Paginator)
    expect(paginators).toHaveLength(2)
    expect(paginators[0].props('totalRecords')).toBe(3)
    expect(paginators[1].props('totalRecords')).toBe(1)
    expect(apiMocks.listInsumos).toHaveBeenCalledWith(PAGE1)
  })

  it('highlights rows below their minimum with a severity tag', async () => {
    const wrapper = await mountView('operador')
    expect(wrapper.text()).toContain('Crítico') // Aceite: stock 2 < half of min 10
  })

  it('operador registers compras via the dialog but sees NO admin insumo actions', async () => {
    const wrapper = await mountView('operador')

    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-insumo"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-insumo"]')).toHaveLength(0)
    expect(apiMocks.listCategorias).not.toHaveBeenCalled() // categorias only for admin form

    await activateTab(wrapper, 'Compras')
    // The create form lives in an el-dialog opened from the toolbar button (FE-DLG-1).
    expect(wrapper.findComponent({ name: 'ComprasForm' }).exists()).toBe(false)
    expect(wrapper.find('[data-test="nueva-compra"]').exists()).toBe(true)
    await wrapper.find('[data-test="nueva-compra"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'ComprasForm' }).exists()).toBe(true)
  })

  it('consulta sees read-only lists only — no compras button, no admin actions', async () => {
    const wrapper = await mountView('consulta')

    const text = wrapper.text()
    expect(text).toContain('Harina de maíz')
    expect(wrapper.find('[data-test="nueva-compra"]').exists()).toBe(false)

    await activateTab(wrapper, 'Compras')
    expect(wrapper.find('[data-test="nueva-compra"]').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'ComprasForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-insumo"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-insumo"]')).toHaveLength(0)
  })

  it('admin owns the insumo dialog button and the edit/delete actions and loads categorias', async () => {
    const wrapper = await mountView('admin')

    // The create form is inside a dialog — closed until the toolbar button opens it.
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(false)
    expect(wrapper.find('[data-test="nuevo-insumo"]').exists()).toBe(true)
    expect(wrapper.findAll('[data-test="edit-insumo"]')).toHaveLength(3)
    expect(wrapper.findAll('[data-test="delete-insumo"]')).toHaveLength(3)
    expect(apiMocks.listCategorias).toHaveBeenCalledTimes(1)
  })

  it('registers a compra with the exact payload and refreshes BOTH tabs (WAC stock change)', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(2) // table page + lookup
    await activateTab(wrapper, 'Compras')

    await wrapper.find('[data-test="nueva-compra"]').trigger('click')
    await nextTick()
    wrapper.findComponent({ name: 'ComprasForm' }).vm.$emit('submit', {
      insumo_id: 1,
      cantidad_comprada: 3,
      precio_unitario_compra: 2500,
    })
    await flushPromises()

    expect(apiMocks.createCompra).toHaveBeenCalledTimes(1)
    expect(apiMocks.createCompra).toHaveBeenCalledWith({
      insumo_id: 1,
      cantidad_comprada: 3,
      precio_unitario_compra: 2500,
    })
    expect(document.body.textContent).toContain('Compra registrada correctamente')

    // WAC ran server-side: BOTH lists refresh (2 calls per load = 4 total).
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(4)
    expect(apiMocks.listCompras).toHaveBeenCalledTimes(2)
  })

  it('filters compras by insumo via the optional insumo_id filter', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Compras')
    expect(apiMocks.listCompras).toHaveBeenCalledWith(PAGE1)

    // Pick 'Aceite' (id 2) from the filter select -> reload with the filter.
    const select = wrapper.find('[data-test="compra-filter-select"]')
    await select.trigger('click')
    await nextTick()
    const option = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
      (el) => el.textContent?.trim() === 'Aceite',
    )
    expect(option).toBeDefined()
    option!.click()
    await flushPromises()

    expect(apiMocks.listCompras).toHaveBeenCalledTimes(2)
    expect(apiMocks.listCompras).toHaveBeenLastCalledWith({ ...PAGE1, insumo_id: 2 })
  })

  it('passes categorias to the insumos table and wires its header filter', async () => {
    const wrapper = await mountView('admin')

    const insumosTable = wrapper.findComponent({ name: 'InsumosTable' })
    expect(insumosTable.props('categorias')).toEqual(CATEGORIAS)

    insumosTable.vm.$emit('filter-change', { categoria_id: 1 })
    await flushPromises()

    expect(apiMocks.listInsumos).toHaveBeenCalledWith({ ...PAGE1, categoria_id: 1 })
  })

  it('passes insumos to the compras table and wires its header filter', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Compras')

    const comprasTable = wrapper.findComponent({ name: 'ComprasTable' })
    expect(comprasTable.props('insumos')).toEqual(INSUMOS)

    comprasTable.vm.$emit('filter-change', { insumo_id: 2 })
    await flushPromises()

    expect(apiMocks.listCompras).toHaveBeenLastCalledWith({ ...PAGE1, insumo_id: 2 })
  })

  it('wires the insumos table sort-change into the API call and resets the page', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listInsumos).toHaveBeenCalledWith(PAGE1)

    wrapper.findComponent({ name: 'InsumosTable' }).vm.$emit('sort-change', { prop: 'stock_actual', order: 'desc' })
    await flushPromises()

    expect(apiMocks.listInsumos).toHaveBeenCalledWith({ ...PAGE1, sort_by: 'stock_actual', order: 'desc' })
  })

  it('wires the compras table sort-change into the API call and resets the page', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Compras')
    expect(apiMocks.listCompras).toHaveBeenCalledWith(PAGE1)

    wrapper
      .findComponent({ name: 'ComprasTable' })
      .vm.$emit('sort-change', { prop: 'precio_unitario_compra', order: 'asc' })
    await flushPromises()

    expect(apiMocks.listCompras).toHaveBeenCalledWith({
      ...PAGE1,
      sort_by: 'precio_unitario_compra',
      order: 'asc',
    })
  })

  it('paging the insumos table refetches with the new offset', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listInsumos).toHaveBeenCalledWith(PAGE1)

    // Emit the page event from the PrimeVue Paginator -> page 2 -> offset 20.
    wrapper.findComponent(Paginator).vm.$emit('page', { first: 20, rows: 20 })
    await flushPromises()

    expect(apiMocks.listInsumos).toHaveBeenCalledWith({ limit: 20, offset: 20 })
  })

  it('global q on the insumos tab resets to page 1 and refetches with q', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listInsumos).toHaveBeenCalledWith(PAGE1)

    const input = wrapper.find('[data-test="insumo-search"]')
    await input.setValue('harina')
    await input.trigger('keyup.enter')
    await flushPromises()

    expect(apiMocks.listInsumos).toHaveBeenCalledWith({ ...PAGE1, q: 'harina' })
  })

  it('opens the create dialog, creates an insumo as admin and refreshes the list', async () => {
    const wrapper = await mountView('admin')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(2)

    await wrapper.find('[data-test="nuevo-insumo"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'InsumoForm' }).vm.$emit('submit', {
      categoria_id: 1,
      nombre: 'Harina de maíz',
      unidad_medida: 'kg',
      stock_actual: 10,
      stock_minimo: 5,
      costo_promedio_actual: 3200,
    })
    await flushPromises()

    expect(apiMocks.createInsumo).toHaveBeenCalledTimes(1)
    expect(apiMocks.createInsumo).toHaveBeenCalledWith({
      categoria_id: 1,
      nombre: 'Harina de maíz',
      unidad_medida: 'kg',
      stock_actual: 10,
      stock_minimo: 5,
      costo_promedio_actual: 3200,
    })
    expect(document.body.textContent).toContain('Insumo creado correctamente')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(4)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(false)
  })

  it('edits an insumo via the edit dialog and closes it on success', async () => {
    const wrapper = await mountView('admin')

    await wrapper.findAll('[data-test="edit-insumo"]')[0].trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Editar insumo')
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(true)
    wrapper.findComponent({ name: 'InsumoForm' }).vm.$emit('submit', {
      categoria_id: 1,
      nombre: 'Harina premium',
      unidad_medida: 'kg',
      stock_actual: 12,
      stock_minimo: 5,
      costo_promedio_actual: 2500,
    })
    await flushPromises()

    expect(apiMocks.updateInsumo).toHaveBeenCalledTimes(1)
    expect(apiMocks.updateInsumo).toHaveBeenCalledWith(
      { insumo_id: 1 },
      {
        categoria_id: 1,
        nombre: 'Harina premium',
        unidad_medida: 'kg',
        stock_actual: 12,
        stock_minimo: 5,
        costo_promedio_actual: 2500,
      },
    )
    expect(document.body.textContent).toContain('Insumo actualizado correctamente')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(4)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(false)
  })

  it('cancels the create dialog without submitting (FE-DLG-2/3)', async () => {
    const wrapper = await mountView('admin')

    await wrapper.find('[data-test="nuevo-insumo"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(true)

    // Esc closes the dialog without a submit (FE-DLG-3).
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushDialogTransition()

    expect(apiMocks.createInsumo).not.toHaveBeenCalled()
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(false)
  })

  it('keeps the dialog open and shows the error when the save fails (FE-DLG-2)', async () => {
    apiMocks.createInsumo.mockRejectedValue({ response: { data: { detail: 'Nombre duplicado' } } })
    const wrapper = await mountView('admin')

    await wrapper.find('[data-test="nuevo-insumo"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'InsumoForm' }).vm.$emit('submit', {
      categoria_id: 1,
      nombre: 'Harina duplicada',
      unidad_medida: 'kg',
      stock_actual: 10,
      stock_minimo: 5,
      costo_promedio_actual: 3200,
    })
    await flushPromises()

    expect(document.body.textContent).toContain('Nombre duplicado')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(2) // no refresh on failure
    // Error keeps the dialog open (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(true)
  })

  it('deletes an insumo after the confirm dialog and refreshes', async () => {
    confirmMocks.confirmAction.mockResolvedValue('accept')
    const wrapper = await mountView('admin')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(2)

    await wrapper.findAll('[data-test="delete-insumo"]')[0].trigger('click')
    await flushPromises()

    expect(apiMocks.deleteInsumo).toHaveBeenCalledTimes(1)
    expect(apiMocks.deleteInsumo).toHaveBeenCalledWith({ insumo_id: 1 })
    expect(document.body.textContent).toContain('Insumo eliminado correctamente')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(4)
  })
})
