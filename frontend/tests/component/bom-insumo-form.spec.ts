/**
 * BomInsumoForm component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL BomInsumoForm with Element Plus in both modes — the BOM
 * insumo line create/edit form for the selected product:
 *  - create: insumo select (insumos prop), cantidad_requerida + optional
 *    porcentaje_desperdicio (0..100); empty insumo / empty cantidad each
 *    block submission with a warning
 *  - a valid create emits the exact BomInsumoCreate body — variante_id
 *    omitted when null (base rule row), included when a variante is picked
 *  - edit mode prefills from the row and emits the update payload
 * The view owns the POST/PUT, the admin-only gate and the refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import BomInsumoForm from '@/components/productos/BomInsumoForm.vue'
import type { components } from '@/types/api.d'
import type { BomInsumoRow } from '@/utils/productos'

type InsumoRead = components['schemas']['InsumoRead']

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
  {
    id: 2,
    categoria_id: 2,
    nombre: 'Aceite',
    unidad_medida: 'L',
    stock_actual: '8.00',
    stock_minimo: '3.00',
    costo_promedio_actual: '9800.00',
    nombre_categoria: 'Abarrotes',
  },
]

const ROW: BomInsumoRow = {
  id: 1,
  insumo: 'Harina de maíz',
  unidad_medida: 'kg',
  cantidad_requerida: '2.00',
  porcentaje_desperdicio: '5.00',
}

async function mountForm(
  mode: 'create' | 'edit' = 'create',
  initial: BomInsumoRow | null = null,
): Promise<VueWrapper> {
  const wrapper = mount(BomInsumoForm, {
    props: { mode, initial, insumos: INSUMOS },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

async function pickInsumo(wrapper: VueWrapper, label: string): Promise<void> {
  const select = wrapper.find('[data-test="bom-insumo-select"]')
  await select.trigger('click')
  await nextTick()
  const item = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`insumo option not found: "${label}"`)
  item.click()
  await nextTick()
  await flushPromises()
}

afterEach(() => {
  ElMessage.closeAll()
  document.body.innerHTML = ''
})

describe('BomInsumoForm (MOD-5)', () => {
  it('renders the fields and the insumo options in create mode', async () => {
    const wrapper = await mountForm('create')

    expect(wrapper.text()).toContain('Insumo')
    expect(wrapper.text()).toContain('Cantidad requerida')
    expect(wrapper.text()).toContain('Desperdicio (%)')

    await wrapper.find('[data-test="bom-insumo-select"]').trigger('click')
    await nextTick()
    const options = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')]
    expect(options.map((o) => o.textContent?.trim())).toEqual(['Harina de maíz', 'Aceite'])
  })

  it('blocks create submission without an insumo', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona el insumo')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create submission with an empty cantidad_requerida', async () => {
    const wrapper = await mountForm('create')

    await pickInsumo(wrapper, 'Harina de maíz')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Indica la cantidad requerida')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact create payload, omitting variante_id when null', async () => {
    const wrapper = await mountForm('create')

    await pickInsumo(wrapper, 'Harina de maíz')
    await wrapper.find('[data-test="cantidad-bom-insumo-input"] input').setValue('2')
    await wrapper.find('[data-test="desperdicio-bom-insumo-input"] input').setValue('5')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      insumo_id: 1,
      cantidad_requerida: 2,
      porcentaje_desperdicio: 5,
    })
  })

  it('edit mode prefills the row and emits the update payload', async () => {
    const wrapper = await mountForm('edit', ROW)

    expect(wrapper.text()).toContain('Harina de maíz') // insumo select prefilled

    await wrapper.find('[data-test="cantidad-bom-insumo-input"] input').setValue('2.5')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      insumo_id: 1,
      cantidad_requerida: 2.5,
      porcentaje_desperdicio: 5,
    })
  })
})
