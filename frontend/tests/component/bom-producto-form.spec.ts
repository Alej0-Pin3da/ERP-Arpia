/**
 * BomProductoForm component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL BomProductoForm with Element Plus in both modes — the
 * combo-content (BomProducto) create/edit form for the selected product:
 *  - create: producto_incluido select (productos prop) + cantidad; empty
 *    selection / empty cantidad each block submission with a warning
 *  - a valid create emits the exact BomProductoCreate body
 *  - edit mode prefills from the row and emits the update payload
 * The view owns the POST/PUT, the admin-only gate and the refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import BomProductoForm from '@/components/productos/BomProductoForm.vue'
import type { components } from '@/types/api.d'
import type { BomProductoRow } from '@/utils/productos'

type ProductoRead = components['schemas']['ProductoRead']

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
    tipo_producto_id: 1,
    nombre: 'Queso campesino',
    requiere_fabricacion: false,
    costos_operativos_fijos: '0.00',
    precio_venta_sugerido: '9000.00',
  },
]

const ROW: BomProductoRow = { id: 1, producto: 'Queso campesino', cantidad: '2.00' }

async function mountForm(
  mode: 'create' | 'edit' = 'create',
  initial: BomProductoRow | null = null,
): Promise<VueWrapper> {
  const wrapper = mount(BomProductoForm, {
    props: { mode, initial, productos: PRODUCTOS },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

async function pickProducto(wrapper: VueWrapper, label: string): Promise<void> {
  const select = wrapper.find('[data-test="bom-producto-select"]')
  await select.trigger('click')
  await nextTick()
  const item = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`producto option not found: "${label}"`)
  item.click()
  await nextTick()
  await flushPromises()
}

afterEach(() => {
  ElMessage.closeAll()
  document.body.innerHTML = ''
})

describe('BomProductoForm (MOD-5)', () => {
  it('renders the fields and the product options in create mode', async () => {
    const wrapper = await mountForm('create')

    expect(wrapper.text()).toContain('Producto incluido')
    expect(wrapper.text()).toContain('Cantidad')

    await wrapper.find('[data-test="bom-producto-select"]').trigger('click')
    await nextTick()
    const options = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')]
    expect(options.map((o) => o.textContent?.trim())).toEqual(['Arepa de choclo', 'Queso campesino'])
  })

  it('blocks create submission without a product', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona el producto incluido')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create submission with an empty cantidad', async () => {
    const wrapper = await mountForm('create')

    await pickProducto(wrapper, 'Queso campesino')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Indica la cantidad')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact create payload', async () => {
    const wrapper = await mountForm('create')

    await pickProducto(wrapper, 'Queso campesino')
    await wrapper.find('[data-test="cantidad-bom-producto-input"] input').setValue('2')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ producto_incluido_id: 2, cantidad: 2 })
  })

  it('edit mode prefills the row and emits the update payload', async () => {
    const wrapper = await mountForm('edit', ROW)

    expect(wrapper.text()).toContain('Queso campesino') // select prefilled

    await wrapper.find('[data-test="cantidad-bom-producto-input"] input').setValue('3')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ producto_incluido_id: 2, cantidad: 3 })
  })
})
