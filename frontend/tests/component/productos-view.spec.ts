/**
 * ProductosView integration tests (PR10, spec MOD-5).
 *
 * Mounts the REAL ProductosView + all productos components against mocked
 * productosApi/tiposProductoApi/insumosApi: the three tabs (Productos / BOM /
 * Costo), the client-joined productos list, role visibility (ALL product,
 * variante and BOM writes are require_admin server-side — operador/consulta
 * see read-only lists, admin owns every form/action), the nested variantes
 * lazy flow (click "Variantes" -> GET /productos/{id}/variantes), the
 * productos create/edit/delete flows (delete expects 204, 409 "in use"
 * surfaced), the BOM tab (select product -> both line lists; admin add with
 * the exact BomInsumoCreate payload; a duplicate line's 409 surfaced) and the
 * Costo tab (select product -> GET /productos/{id}/costo -> grouped tree +
 * grand total; optional variante select adds ?variante_id).
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage, ElMessageBox } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

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

async function mountView(rol: string): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 2, nombre: 'Pepe', email: 'pepe@arpia.com.co', rol },
  })
  const wrapper = mount(ProductosView, { global: { plugins: [pinia, ElementPlus] } })
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

describe('ProductosView (MOD-5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMocks.listProductos.mockResolvedValue(PRODUCTOS)
    apiMocks.listTipos.mockResolvedValue(TIPOS)
    apiMocks.listInsumos.mockResolvedValue(INSUMOS)
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

    expect(apiMocks.listProductos).toHaveBeenCalledTimes(1)
    expect(apiMocks.listProductos).toHaveBeenCalledWith({ limit: 1000 })
    expect(apiMocks.listTipos).toHaveBeenCalledTimes(1)
  })

  it('operador sees read-only lists — no product form, no edit/delete/variantes actions', async () => {
    const wrapper = await mountView('operador')

    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-producto"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-producto"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="producto-variantes"]')).toHaveLength(0)
  })

  it('consulta is read-only everywhere', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-producto"]')).toHaveLength(0)

    await activateTab(wrapper, 'BOM')
    expect(wrapper.findComponent({ name: 'BomInsumoForm' }).exists()).toBe(false)
    expect(wrapper.findAll('[data-test="edit-bom-insumo"]')).toHaveLength(0)
  })

  it('admin owns the product form, the edit/delete actions and the variantes button', async () => {
    const wrapper = await mountView('admin')

    expect(wrapper.findComponent({ name: 'ProductoForm' }).exists()).toBe(true)
    expect(wrapper.findAll('[data-test="edit-producto"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="delete-producto"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="producto-variantes"]')).toHaveLength(2)
  })

  it('creates a product with the exact payload and refreshes the list', async () => {
    const wrapper = await mountView('admin')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(1)

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
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2)
  })

  it('edits a product via the inline edit form and returns to the create form', async () => {
    const wrapper = await mountView('admin')

    await wrapper.findAll('[data-test="edit-producto"]')[0].trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Editar producto')
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
    expect(wrapper.text()).toContain('Crear producto') // back to create form
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2)
  })

  it('deletes a product after the confirm dialog (204) and refreshes', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    const wrapper = await mountView('admin')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(1)

    await wrapper.findAll('[data-test="delete-producto"]')[0].trigger('click')
    await flushPromises()

    expect(apiMocks.deleteProducto).toHaveBeenCalledTimes(1)
    expect(apiMocks.deleteProducto).toHaveBeenCalledWith({ producto_id: 1 })
    expect(document.body.textContent).toContain('Producto eliminado correctamente')
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(2)
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
    expect(apiMocks.listProductos).toHaveBeenCalledTimes(1) // no refresh after failure
  })

  it('lazily loads the nested variantes and adds one with the exact payload', async () => {
    const wrapper = await mountView('admin')

    await wrapper.findAll('[data-test="producto-variantes"]')[0].trigger('click')
    await flushPromises()

    expect(apiMocks.listVariantes).toHaveBeenCalledTimes(1)
    expect(apiMocks.listVariantes).toHaveBeenCalledWith({ producto_id: 1 })
    expect(wrapper.text()).toContain('Individual')
    expect(wrapper.text()).toContain('$13.000,00')
    expect(wrapper.text()).toContain('—') // null precio_venta

    wrapper.findComponent({ name: 'VarianteForm' }).vm.$emit('submit', { nombre_variante: 'Docena' })
    await flushPromises()

    expect(apiMocks.createVariante).toHaveBeenCalledTimes(1)
    expect(apiMocks.createVariante).toHaveBeenCalledWith({ producto_id: 1 }, { nombre_variante: 'Docena' })
    expect(document.body.textContent).toContain('Variante creada correctamente')
    expect(apiMocks.listVariantes).toHaveBeenCalledTimes(2) // refresh after create
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

  it('BOM admin adds an insumo line and surfaces the duplicate 409', async () => {
    const wrapper = await mountView('admin')
    await activateTab(wrapper, 'BOM')
    await wrapper.find('[data-test="bom-product-select"]').trigger('click')
    await nextTick()
    await pickOption('bom-product-popper', 'Arepa de choclo')

    expect(wrapper.findComponent({ name: 'BomInsumoForm' }).exists()).toBe(true)
    expect(wrapper.findAll('[data-test="edit-bom-insumo"]')).toHaveLength(1)

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

    // Duplicate line -> backend 409 surfaced via server detail.
    apiMocks.createBomInsumo.mockRejectedValueOnce({
      response: { data: { detail: 'BomInsumo line already exists for this product, insumo and variant' } },
    })
    wrapper.findComponent({ name: 'BomInsumoForm' }).vm.$emit('submit', {
      insumo_id: 1,
      cantidad_requerida: 2,
      porcentaje_desperdicio: 5,
    })
    await flushPromises()

    expect(document.body.textContent).toContain('BomInsumo line already exists for this product, insumo and variant')
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
