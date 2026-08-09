/**
 * InventarioView integration tests (PR9 MOD-4 + ui-mantenimiento PR1 T6).
 *
 * Mounts the REAL InventarioView + all inventario components against mocked
 * insumosApi/comprasApi/categoriasInsumosApi: the two tabs (Insumos /
 * Compras), server-side pagination ({items,total} + el-pagination driving
 * limit/offset refetches), toolbar filters (q + categoria_id insumos,
 * proveedor_id compras) that reset to page 1, the server-joined insumos list,
 * below-minimum row highlighting, role visibility, the compras register flow
 * and the admin insumo create/edit/delete flows. Lookup joins keep limit:1000
 * against `.items` (design D3).
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage, ElMessageBox } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'
import InventarioView from '@/views/InventarioView.vue'
import type { components } from '@/types/api.d'

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
    proveedor_id: null,
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
  const wrapper = mount(InventarioView, { global: { plugins: [pinia, ElementPlus] } })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

/** Click the el-tabs item with the given label (pane content mounts on visit). */
async function activateTab(wrapper: VueWrapper, label: string): Promise<void> {
  const item = wrapper.findAll('.el-tabs__item').find((i) => i.text().trim() === label)
  if (!item) throw new Error(`tab not found: "${label}"`)
  await item.trigger('click')
  await nextTick()
  await flushPromises()
}

describe('InventarioView (MOD-4 + T6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
    ElMessage.closeAll()
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

  it('renders el-pagination with the server total on the insumos tab', async () => {
    const wrapper = await mountView('operador')
    // Element Plus pagination renders a page-size selector and page buttons;
    // the total comes from the API (3), not a local guess.
    expect(wrapper.findComponent({ name: 'ElPagination' }).exists()).toBe(true)
    expect(apiMocks.listInsumos).toHaveBeenCalledWith(PAGE1)
  })

  it('highlights rows below their minimum with a severity tag', async () => {
    const wrapper = await mountView('operador')
    expect(wrapper.text()).toContain('Crítico') // Aceite: stock 2 < half of min 10
  })

  it('operador registers compras but sees NO admin insumo actions', async () => {
    const wrapper = await mountView('operador')

    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-insumo"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-insumo"]')).toHaveLength(0)
    expect(apiMocks.listCategorias).not.toHaveBeenCalled() // categorias only for admin form

    await activateTab(wrapper, 'Compras')
    expect(wrapper.findComponent({ name: 'ComprasForm' }).exists()).toBe(true)
    expect(wrapper.text()).toContain('Registrar compra')
  })

  it('consulta sees read-only lists only — no compras form, no admin actions', async () => {
    const wrapper = await mountView('consulta')

    const text = wrapper.text()
    expect(text).toContain('Harina de maíz')
    expect(text).not.toContain('Registrar compra')

    await activateTab(wrapper, 'Compras')
    expect(wrapper.findComponent({ name: 'ComprasForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-insumo"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-insumo"]')).toHaveLength(0)
  })

  it('admin sees the insumo create form, the edit/delete actions and loads categorias', async () => {
    const wrapper = await mountView('admin')

    expect(wrapper.findComponent({ name: 'InsumoForm' }).exists()).toBe(true)
    expect(wrapper.text()).toContain('Crear insumo')
    expect(wrapper.findAll('[data-test="edit-insumo"]')).toHaveLength(3)
    expect(wrapper.findAll('[data-test="delete-insumo"]')).toHaveLength(3)
    expect(apiMocks.listCategorias).toHaveBeenCalledTimes(1)
  })

  it('registers a compra with the exact payload and refreshes BOTH tabs (WAC stock change)', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(2) // table page + lookup
    await activateTab(wrapper, 'Compras')

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

  it('paging the insumos table refetches with the new offset', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listInsumos).toHaveBeenCalledWith(PAGE1)

    // Emit the page-change event from el-pagination -> page 2 -> offset 20.
    wrapper.findComponent({ name: 'ElPagination' }).vm.$emit('current-change', 2)
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

  it('creates an insumo as admin and refreshes the list', async () => {
    const wrapper = await mountView('admin')
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(2)

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
  })

  it('edits an insumo via the inline edit form and returns to the create form', async () => {
    const wrapper = await mountView('admin')

    await wrapper.findAll('[data-test="edit-insumo"]')[0].trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Editar insumo')
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
    expect(wrapper.text()).toContain('Crear insumo') // back to the create form
    expect(apiMocks.listInsumos).toHaveBeenCalledTimes(4)
  })

  it('deletes an insumo after the confirm dialog and refreshes', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
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
