/**
 * ProductoForm component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL ProductoForm with Element Plus in both modes:
 *  - create: tipo select (GET /tipos-producto), nombre, requiere_fabricacion
 *    switch (default on), costos_operativos_fijos + precio_venta_sugerido
 *    number fields; empty nombre / no tipo each block submission with a
 *    warning
 *  - a valid create emits the exact ProductoCreate body; a valid edit emits
 *    the exact ProductoUpdate body (all fields editable — the backend PUT
 *    schema accepts the full set)
 * The view owns the POST/PUT, the admin-only gate and the refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import ProductoForm from '@/components/productos/ProductoForm.vue'
import type { components } from '@/types/api.d'

type TipoProductoRead = components['schemas']['TipoProductoRead']
type ProductoRead = components['schemas']['ProductoRead']

const TIPOS: TipoProductoRead[] = [
  { id: 1, nombre: 'Alimentos' },
  { id: 2, nombre: 'Aseo' },
]

const PRODUCTO: ProductoRead = {
  id: 1,
  tipo_producto_id: 1,
  nombre: 'Arepa de choclo',
  requiere_fabricacion: true,
  costos_operativos_fijos: '5000.00',
  precio_venta_sugerido: '12000.00',
}

async function mountForm(
  mode: 'create' | 'edit' = 'create',
  initial: ProductoRead | null = null,
): Promise<VueWrapper> {
  const wrapper = mount(ProductoForm, {
    props: { mode, initial, tipos: TIPOS },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

async function pickTipo(wrapper: VueWrapper, label: string): Promise<void> {
  const select = wrapper.find('[data-test="tipo-producto-select"]')
  await select.trigger('click')
  await nextTick()
  const item = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`tipo option not found: "${label}"`)
  item.click()
  await nextTick()
  await flushPromises()
}

afterEach(() => {
  ElMessage.closeAll()
  document.body.innerHTML = ''
})

describe('ProductoForm (MOD-5)', () => {
  it('renders the five fields and the tipo options in create mode', async () => {
    const wrapper = await mountForm('create')

    const text = wrapper.text()
    expect(text).toContain('Tipo de producto')
    expect(text).toContain('Nombre del producto')
    expect(text).toContain('Requiere fabricación')
    expect(text).toContain('Costos operativos fijos')
    expect(text).toContain('Precio de venta sugerido')

    await wrapper.find('[data-test="tipo-producto-select"]').trigger('click')
    await nextTick()
    const options = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')]
    expect(options.map((o) => o.textContent?.trim())).toEqual(['Alimentos', 'Aseo'])
  })

  it('blocks create submission with an empty nombre', async () => {
    const wrapper = await mountForm('create')

    await pickTipo(wrapper, 'Alimentos')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe el nombre del producto')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create submission without a tipo', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-producto-input"]').setValue('Detergente')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona el tipo de producto')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact create payload with requiere_fabricacion default on', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-producto-input"]').setValue('Arepa de choclo')
    await pickTipo(wrapper, 'Alimentos')
    await wrapper.find('[data-test="costos-fijos-input"] input').setValue('5000')
    await wrapper.find('[data-test="precio-venta-input"] input').setValue('12000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      tipo_producto_id: 1,
      nombre: 'Arepa de choclo',
      requiere_fabricacion: true,
      costos_operativos_fijos: 5000,
      precio_venta_sugerido: 12000,
    })
  })

  it('edit mode prefills every field from the row and emits the exact update payload', async () => {
    const wrapper = await mountForm('edit', PRODUCTO)

    expect((wrapper.find('[data-test="nombre-producto-input"]').element as HTMLInputElement).value).toBe(
      'Arepa de choclo',
    )
    expect(wrapper.text()).toContain('Alimentos') // tipo select prefilled

    await wrapper.find('[data-test="nombre-producto-input"]').setValue('Arepa de choclo premium')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      tipo_producto_id: 1,
      nombre: 'Arepa de choclo premium',
      requiere_fabricacion: true,
      costos_operativos_fijos: 5000,
      precio_venta_sugerido: 12000,
    })
  })
})
