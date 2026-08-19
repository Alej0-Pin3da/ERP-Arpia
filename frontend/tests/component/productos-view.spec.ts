/**
 * ProductosView integration tests (PR10 MOD-5 + ui-mantenimiento PR1 T6).
 *
 * Mounts the REAL ProductosView + all productos components against mocked
 * productosApi/tiposProductoApi/insumosApi: the three tabs (Productos / BOM /
 * Costo), the client-joined productos list with server-side pagination
 * ({items,total} + PrimeVue Paginator + q/tipo filters), role visibility (ALL
 * product, variante and BOM writes are require_admin server-side), the nested
 * variantes lazy flow, the productos create/edit/delete flows, the BOM tab and
 * the Costo tab. Lookup joins (BOM/Costo selects, tipo/insumo labels) keep
 * limit:1000 against `.items` (design D3). el-tabs/el-dialog stay until S2.
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
import ProductosView from '@/views/ProductosView.vue'
import type { components } from '@/types/api.d'

type ProductoRead = components['schemas']['ProductoRead']
type TipoProductoRead = components['schemas']['TipoProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']
type BomInsumoRead = components['schemas']['BomInsumoRead']
type BomProductoRead = components['schemas']['BomProductoRead']
type InsumoRead = components['schemas']['InsumoRead']
type CostoProduccionRead = components['schemas']['CostoProduccionRead']

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listProductos: vi.fn(),
    createProducto: vi.fn(),
    updateProducto: vi.fn(),
    deleteProducto: vi.fn(),
    listVariantes: vi.fn(),
    createVariante: vi.fn(),
    updateVariante: vi.fn(),
    deleteVariante: vi.fn(),
    listBomInsumos: vi.fn(),
    createBomInsumo: vi.fn(),
    updateBomInsumo: vi.fn(),
    deleteBomInsumo: vi.fn(),
    listBomProductos: vi.fn(),
    createBomProducto: vi.fn(),
    updateBomProducto: vi.fn(),
    deleteBomProducto: vi.fn(),
    costo: vi.fn(),
    listTipos: vi.fn(),
    listInsumos: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  productosApi: {
    list: apiMocks.listProductos,
    create: apiMocks.createProducto,
    update: apiMocks.updateProducto,
    delete: apiMocks.deleteProducto,
    listVariantes: apiMocks.listVariantes,
    createVariante: apiMocks.createVariante,
    updateVariante: apiMocks.updateVariante,
    deleteVariante: apiMocks.deleteVariante,
    listBomInsumos: apiMocks.listBomInsumos,
    createBomInsumo: apiMocks.createBomInsumo,
    updateBomInsumo: apiMocks.updateBomInsumo,
    deleteBomInsumo: apiMocks.deleteBomInsumo,
    listBomProductos: apiMocks.listBomProductos,
    createBomProducto: apiMocks.createBomProducto,
    updateBomProducto: apiMocks.updateBomProducto,
    deleteBomProducto: apiMocks.deleteBomProducto,
    costo: apiMocks.costo,
  },
  tiposProductoApi: { list: apiMocks.listTipos },
  insumosApi: { list: apiMocks.listInsumos },
}))

const TIPOS: TipoProductoRead[] = [{ id: 1, nombre: 'Alimentos' }]

const PRODUCTOS: ProductoRead[] = [
  {
    id: 1,
    tipo_producto_id: 1,
    nombre: 'Arepa de choclo',
    requiere_fabricacion: true,
    costos_operativos_fijos: '5000.00',
    precio_venta_sugerido: '12000.00',
  },
  {
    id: 2,
    tipo_producto_id: 99, // tipo gone -> 'Tipo #99' fallback
    nombre: 'Detergente',
    requiere_fabricacion: false,
    costos_operativos_fijos: '0.00',
    precio_venta_sugerido: '8000.00',
  },
]

const VARIANTES: VarianteProductoRead[] = [
  { id: 1, producto_id: 1, nombre_variante: 'Individual', precio_venta: '13000.00' },
  { id: 2, producto_id: 1, nombre_variante: 'Docena', precio_venta: null },
]

const INSUMOS: InsumoRead[] = [
  {
    id: 1,
    categoria_id: 1,
    nombre: 'Harina de maíz',
    unidad_medida: 'kg',
    stock_actual: '12.00',
    stock_minimo: '5.00',
    costo_promedio_actual: '2500.00',
    nombre_categoria: 'Granos',
  },
]

const BOM_INSUMOS: BomInsumoRead[] = [
  {
    id: 1,
    producto_id: 1,
    insumo_id: 1,
    variante_id: null,
    cantidad_requerida: '2.00',
    porcentaje_desperdicio: '5.00',
  },
]

const BOM_PRODUCTOS: BomProductoRead[] = [
  { id: 1, combo_id: 1, producto_incluido_id: 2, cantidad: '2.00' },
]

const COSTO: CostoProduccionRead = {
  total: '15200.00',
  lineas: [
    { tipo: 'insumo', id: 1, nombre: 'Harina de maíz', cantidad: '2.10', costo_unitario: '2500.00', costo_total: '5250.00' },
    { tipo: 'operativos_fijos', id: 1, nombre: 'Arepa de choclo', cantidad: '1.00', costo_unitario: '5000.00', costo_total: '5000.00' },
    { tipo: 'producto', id: 2, nombre: 'Detergente', cantidad: '1.00', costo_unitario: '4950.00', costo_total: '4950.00' },
  ],
}

/** Table page default (page 1, pageSize 20). */
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
  const wrapper = mount(ProductosView, {
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

/**
 * Pick an option in the dropdown of a specific select. The view keeps every
 * el-tab-pane mounted, so several selects share the DOM — scope the lookup to
 * the select's `popper-class` (`.{popperClass} .el-select-dropdown__item`)
 * instead of a document-wide query.
 */
async function pickOption(popperClass: string, label: string): Promise<void> {
  const option = [...document.querySelectorAll<HTMLElement>(`.${popperClass} .el-select-dropdown__item`)].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!option) throw new Error(`option not found in ${popperClass}: "${label}"`)
  option.click()
  await nextTick()
  await flushPromises()
}

/** Let the el-dialog leave transition finish (Vue's nextFrame is a double rAF). */
async function flushDialogTransition(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

describe('ProductosView (MOD-5 + T6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Table page uses the {items,total} contract; lookups keep limit:1000.
    apiMocks.listProductos.mockResolvedValue({ items: PRODUCTOS, total: 2 })
    apiMocks.listTipos.mockResolvedValue({ items: TIPOS, total: 1 })
    apiMocks.listInsumos.mockResolvedValue({ items: INSUMOS, total: 1 })
    apiMocks.listVariantes.mockResolvedValue(VARIANTES)
    apiMocks.listBomInsumos.mockResolvedValue(BOM_INSUMOS)
    apiMocks.listBomProductos.mockResolvedValue(BOM_PRODUCTOS)
    apiMocks.costo.mockResolvedValue(COSTO)
    apiMocks.createProducto.mockResolvedValue(PRODUCTOS[0])
    apiMocks.updateProducto.mockResolvedValue({ ...PRODUCTOS[0], nombre: 'Arepa premium' })
    apiMocks.deleteProducto.mockResolvedValue(undefined)
    apiMocks.createVariante.mockResolvedValue(VARIANTES[0])
    apiMocks.updateVariante.mockResolvedValue({ ...VARIANTES[0], nombre_variante: 'Individual premium' })
    apiMocks.deleteVariante.mockResolvedValue(undefined)
    apiMocks.createBomInsumo.mockResolvedValue(BOM_INSUMOS[0])
    apiMocks.updateBomInsumo.mockResolvedValue(BOM_INSUMOS[0])
    apiMocks.deleteBomInsumo.mockResolvedValue(undefined)
    apiMocks.createBomProducto.mockResolvedValue(BOM_PRODUCTOS[0])
    apiMocks.updateBomProducto.mockResolvedValue(BOM_PRODUCTOS[0])
    apiMocks.deleteBomProducto.mockResolvedValue(undefined)
  })

  afterEach(() => {
    ElMessage.closeAll()
    vi.restoreAllMocks()
  })

  it('renders the three tabs and the client-joined productos list for an operador', async () => {
    const wrapper = await mountView('operador')

    const text = wrapper.text()
    expect(text).toContain('Productos')
    expect(text).toContain('BOM')
    expect(text).toContain('Costo')

    expect(text).toContain('Arepa de choclo')
    expect(text).toContain('Alimentos') // client-joined tipo label
    expect(text).toContain('Tipo #99') // fallback
    expect(text).toContain('$12.000,00') // precio_venta_sugerido es-CO

    // Table fetch pages; the lookup join keeps limit:1000.
    expect(apiMocks.listProductos).toHaveBeenCalledWith(PAGE1)
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listTipos).toHaveBeenCalledTimes(1)
  })

  it('renders Paginator on the productos tab and pages with offset', async () => {
    const wrapper = await mountView('operador')
    expect(wrapper.findComponent(Paginator).exists()).toBe(true)
    expect(apiMocks.listProductos).toHaveBeenCalledWith(PAGE1)

    wrapper.findComponent(Paginator).vm.$emit('page', { first: 20, rows: 20 })
    await flushPromises()
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 20, offset: 20 })
  })

  it('global q on the productos tab resets to page 1 and refetches with q', async () => {
    const wrapper = await mountView('operador')

    const input = wrapper.find('[data-test="producto-search"]')
    await input.setValue('arepa')
    await input.trigger('keyup.enter')
    await flushPromises()

    expect(apiMocks.listProductos).toHaveBeenCalledWith({ ...PAGE1, q: 'arepa' })
  })

  it('wires the productos table sort-change into server-side sort params', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listProductos).toHaveBeenCalledWith(PAGE1)

    wrapper
      .findComponent({ name: 'ProductosTable' })
      .vm.$emit('sort-change', { prop: 'precio_venta_sugerido', order: 'desc' })
    await flushPromises()

    // productos is fetched twice per load (table page + lookup): 2 + 2.
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(4)
    expect(apiMocks.listProductos).toHaveBeenCalledWith({
      ...PAGE1,
      sort_by: 'precio_venta_sugerido',
      order: 'desc',
    })
  })

  it('operador sees read-only lists — no product form, no edit/delete/variantes actions', async () => {
    const wrapper = await mountView('operador')

    expect(wrapper.find('[data-test="nuevo-producto"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-producto"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-producto"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="producto-variantes"]')).toHaveLength(0)
  })

  it('consulta is read-only everywhere', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.find('[data-test="nuevo-producto"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-producto"]')).toHaveLength(0)

    await activateTab(wrapper, 'BOM')
    expect(wrapper.find('[data-test="nueva-linea-insumo"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-bom-insumo"]')).toHaveLength(0)
  })

  it('admin owns the dialog buttons, the edit/delete actions and the variantes button', async () => {
    const wrapper = await mountView('admin')

    // The create form lives in an el-dialog — closed until the button opens it (FE-DLG-1).
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(false)
    expect(wrapper.find('[data-test="nuevo-producto"]').exists()).toBe(true)
    expect(wrapper.findAll('[data-test="edit-producto"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="delete-producto"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="producto-variantes"]')).toHaveLength(2)
  })

  it('opens the create dialog, creates a product with the exact payload and refreshes the list', async () => {
    const wrapper = await mountView('admin')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2) // table page + lookup

    await wrapper.find('[data-test="nuevo-producto"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'ProductoForm' }).vm.$emit('submit', {
      tipo_producto_id: 1,
      nombre: 'Arepa de choclo',
      requiere_fabricacion: true,
      costos_operativos_fijos: 5000,
      precio_venta_sugerido: 12000,
    })
    await flushPromises()

    expect(apiMocks.createProducto).toHaveBeenCalledTimes(1)
    expect(apiMocks.createProducto).toHaveBeenCalledWith({
      tipo_producto_id: 1,
      nombre: 'Arepa de choclo',
      requiere_fabricacion: true,
      costos_operativos_fijos: 5000,
      precio_venta_sugerido: 12000,
    })
    expect(document.body.textContent).toContain('Producto creado correctamente')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(4)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(false)
  })

  it('edits a product via the edit dialog and closes it on success', async () => {
    const wrapper = await mountView('admin')

    await wrapper.findAll('[data-test="edit-producto"]')[0].trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Editar producto')
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(true)
    wrapper.findComponent({ name: 'ProductoForm' }).vm.$emit('submit', {
      tipo_producto_id: 1,
      nombre: 'Arepa premium',
      requiere_fabricacion: true,
      costos_operativos_fijos: 5000,
      precio_venta_sugerido: 12000,
    })
    await flushPromises()

    expect(apiMocks.updateProducto).toHaveBeenCalledTimes(1)
    expect(apiMocks.updateProducto).toHaveBeenCalledWith(
      { producto_id: 1 },
      {
        tipo_producto_id: 1,
        nombre: 'Arepa premium',
        requiere_fabricacion: true,
        costos_operativos_fijos: 5000,
        precio_venta_sugerido: 12000,
      },
    )
    expect(document.body.textContent).toContain('Producto actualizado correctamente')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(4)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(false)
  })

  it('cancels the create dialog without submitting (FE-DLG-2/3)', async () => {
    const wrapper = await mountView('admin')

    await wrapper.find('[data-test="nuevo-producto"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(true)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushDialogTransition()

    expect(apiMocks.createProducto).not.toHaveBeenCalled()
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(false)
  })

  it('keeps the product dialog open and shows the error when the save fails (FE-DLG-2)', async () => {
    apiMocks.createProducto.mockRejectedValue({ response: { data: { detail: 'Nombre duplicado' } } })
    const wrapper = await mountView('admin')

    await wrapper.find('[data-test="nuevo-producto"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'ProductoForm' }).vm.$emit('submit', {
      tipo_producto_id: 1,
      nombre: 'Arepa duplicada',
      requiere_fabricacion: true,
      costos_operativos_fijos: 5000,
      precio_venta_sugerido: 12000,
    })
    await flushPromises()

    expect(document.body.textContent).toContain('Nombre duplicado')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2) // no refresh on failure
    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(true)
  })

  it('deletes a product after the confirm dialog (204) and refreshes', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    const wrapper = await mountView('admin')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2)

    await wrapper.findAll('[data-test="delete-producto"]')[0].trigger('click')
    await flushPromises()

    expect(apiMocks.deleteProducto).toHaveBeenCalledTimes(1)
    expect(apiMocks.deleteProducto).toHaveBeenCalledWith({ producto_id: 1 })
    expect(document.body.textContent).toContain('Producto eliminado correctamente')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(4)
  })

  it('surfaces the 409 when deleting a product that is in use', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    apiMocks.deleteProducto.mockRejectedValue({
      response: { data: { detail: 'Producto is in use and cannot be deleted' } },
    })
    const wrapper = await mountView('admin')

    await wrapper.findAll('[data-test="delete-producto"]')[0].trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('Producto is in use and cannot be deleted')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2) // no refresh after failure
  })

  it('lazily loads the nested variantes and adds one via the dialog with the exact payload', async () => {
    const wrapper = await mountView('admin')

    await wrapper.findAll('[data-test="producto-variantes"]')[0].trigger('click')
    await flushPromises()

    expect(apiMocks.listVariantes).toHaveBeenCalledTimes(1)
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 1 })
    expect(wrapper.text()).toContain('Individual')
    expect(wrapper.text()).toContain('$13.000,00')
    expect(wrapper.text()).toContain('—') // null precio_venta

    // The variante form lives in an el-dialog opened from the section button (FE-DLG-1).
    expect(wrapper.findComponent({ name: 'VarianteForm' }).exists()).toBe(false)
    await wrapper.find('[data-test="nueva-variante"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'VarianteForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'VarianteForm' }).vm.$emit('submit', { nombre_variante: 'Docena' })
    await flushPromises()

    expect(apiMocks.createVariante).toHaveBeenCalledTimes(1)
    expect(apiMocks.createVariante).toHaveBeenCalledWith({ producto_id: 1 }, { nombre_variante: 'Docena' })
    expect(document.body.textContent).toContain('Variante creada correctamente')
    expect(apiMocks.listVariantes).toHaveBeenCalledTimes(2) // refresh after create
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'VarianteForm' }).exists()).toBe(false)
  })

  it('BOM tab loads both line lists for the selected product', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'BOM')

    await wrapper.find('[data-test="bom-product-select"]').trigger('click')
    await nextTick()
    await pickOption('bom-product-popper', 'Arepa de choclo')

    expect(apiMocks.listBomInsumos).toHaveBeenCalledTimes(1)
    expect(apiMocks.listBomInsumos).toHaveBeenCalledWith({ producto_id: 1 })
    expect(apiMocks.listBomProductos).toHaveBeenCalledTimes(1)
    expect(apiMocks.listBomProductos).toHaveBeenCalledWith({ producto_id: 1 })
    expect(wrapper.text()).toContain('Harina de maíz') // joined insumo name
    expect(wrapper.text()).toContain('Detergente') // joined included product
  })

  it('BOM admin adds an insumo line via the dialog and surfaces the duplicate 409', async () => {
    const wrapper = await mountView('admin')
    await activateTab(wrapper, 'BOM')
    await wrapper.find('[data-test="bom-product-select"]').trigger('click')
    await nextTick()
    await pickOption('bom-product-popper', 'Arepa de choclo')

    // The BOM line forms live in el-dialogs opened from the section buttons (FE-DLG-1).
    expect(wrapper.findComponent({ name: 'BomInsumoForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-bom-insumo"]')).toHaveLength(1)
    await wrapper.find('[data-test="nueva-linea-insumo"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'BomInsumoForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'BomInsumoForm' }).vm.$emit('submit', {
      insumo_id: 1,
      cantidad_requerida: 2,
      porcentaje_desperdicio: 5,
    })
    await flushPromises()

    expect(apiMocks.createBomInsumo).toHaveBeenCalledTimes(1)
    expect(apiMocks.createBomInsumo).toHaveBeenCalledWith(
      { producto_id: 1 },
      { insumo_id: 1, cantidad_requerida: 2, porcentaje_desperdicio: 5 },
    )
    expect(document.body.textContent).toContain('Línea de BOM agregada correctamente')
    expect(apiMocks.listBomInsumos).toHaveBeenCalledTimes(2) // refresh after create
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'BomInsumoForm' }).exists()).toBe(false)

    // Duplicate line -> backend 409 surfaced via server detail (dialog stays open).
    apiMocks.createBomInsumo.mockRejectedValueOnce({
      response: { data: { detail: 'BomInsumo line already exists for this product, insumo and variant' } },
    })
    await wrapper.find('[data-test="nueva-linea-insumo"]').trigger('click')
    await nextTick()
    wrapper.findComponent({ name: 'BomInsumoForm' }).vm.$emit('submit', {
      insumo_id: 1,
      cantidad_requerida: 2,
      porcentaje_desperdicio: 5,
    })
    await flushPromises()

    expect(document.body.textContent).toContain('BomInsumo line already exists for this product, insumo and variant')
    expect(wrapper.findComponent({ name: 'BomInsumoForm' }).exists()).toBe(true)
  })

  it('BOM admin adds a combo line via the dialog with the exact payload (FE-DLG-1/2)', async () => {
    const wrapper = await mountView('admin')
    await activateTab(wrapper, 'BOM')
    await wrapper.find('[data-test="bom-product-select"]').trigger('click')
    await nextTick()
    await pickOption('bom-product-popper', 'Arepa de choclo')

    expect(wrapper.findComponent({ name: 'BomProductoForm' }).exists()).toBe(false)
    await wrapper.find('[data-test="nueva-linea-combo"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'BomProductoForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'BomProductoForm' }).vm.$emit('submit', {
      producto_incluido_id: 2,
      cantidad: 2,
    })
    await flushPromises()

    expect(apiMocks.createBomProducto).toHaveBeenCalledTimes(1)
    expect(apiMocks.createBomProducto).toHaveBeenCalledWith(
      { producto_id: 1 },
      { producto_incluido_id: 2, cantidad: 2 },
    )
    expect(document.body.textContent).toContain('Línea de combo agregada correctamente')
    expect(apiMocks.listBomProductos).toHaveBeenCalledTimes(2) // refresh after create
    expect(wrapper.findComponent({ name: 'BomProductoForm' }).exists()).toBe(false)
  })

  it('Costo tab renders the grouped tree with the grand total', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Costo')

    await wrapper.find('[data-test="costo-product-select"]').trigger('click')
    await nextTick()
    await pickOption('costo-product-popper', 'Arepa de choclo')

    expect(apiMocks.costo).toHaveBeenCalledTimes(1)
    expect(apiMocks.costo).toHaveBeenCalledWith({ producto_id: 1 }, undefined)

    const text = wrapper.text()
    expect(text).toContain('Insumos')
    expect(text).toContain('Productos')
    expect(text).toContain('Costos operativos fijos')
    expect(text).toContain('Harina de maíz')
    expect(text).toContain('Costo total de producción')
    expect(text).toContain('$15.200,00') // grand total
  })

  it('Costo tab passes the optional variante_id when a variante is selected', async () => {
    const wrapper = await mountView('operador')
    await activateTab(wrapper, 'Costo')

    await wrapper.find('[data-test="costo-product-select"]').trigger('click')
    await nextTick()
    await pickOption('costo-product-popper', 'Arepa de choclo')
    expect(apiMocks.costo).toHaveBeenLastCalledWith({ producto_id: 1 }, undefined)

    // Variante select appears once variantes are loaded for the product.
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 1 })
    await wrapper.find('[data-test="costo-variante-select"]').trigger('click')
    await nextTick()
    await pickOption('costo-variante-popper', 'Individual')
    await flushPromises()

    expect(apiMocks.costo).toHaveBeenCalledTimes(2)
    expect(apiMocks.costo).toHaveBeenLastCalledWith({ producto_id: 1 }, { variante_id: 1 })
  })
})
