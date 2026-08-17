/**
 * InsumoForm component tests (PR9, spec MOD-4).
 *
 * Mounts the REAL InsumoForm with PrimeVue in both modes:
 *  - create: nombre, categoria select (GET /categorias-insumos), unidad_medida
 *    and the three stock/cost number fields; empty nombre / no categoria /
 *    empty unidad each block submission with a warning
 *  - edit: all fields prefilled from the row and editable (the backend PUT
 *    schema accepts every field — unlike socios, nothing is read-only)
 *  - a valid create emits the exact InsumoCreate body; a valid edit emits the
 *    exact InsumoUpdate body
 * The view owns the POST/PUT, the admin-only gate and the refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import InsumoForm from '@/components/inventario/InsumoForm.vue'
import type { components } from '@/types/api.d'

type InsumoRead = components['schemas']['InsumoRead']
type CategoriaInsumoRead = components['schemas']['CategoriaInsumoRead']

const CATEGORIAS: CategoriaInsumoRead[] = [
  { id: 1, nombre: 'Granos' },
  { id: 2, nombre: 'Abarrotes' },
]

const INSUMO: InsumoRead = {
  id: 1,
  categoria_id: 1,
  nombre: 'Harina de maíz',
  unidad_medida: 'kg',
  stock_actual: '12.00',
  stock_minimo: '5.00',
  costo_promedio_actual: '2500.00',
  nombre_categoria: 'Granos',
}

async function mountForm(
  mode: 'create' | 'edit' = 'create',
  initial: InsumoRead | null = null,
): Promise<VueWrapper> {
  const wrapper = mount(InsumoForm, {
    props: { mode, initial, categorias: CATEGORIAS },
    global: {
      plugins: [
        ElementPlus,
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  return wrapper
}

/** Let a PrimeVue Select overlay open (Teleport + transition) before interacting. */
async function flushOverlay(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

async function pickCategoria(wrapper: VueWrapper, label: string): Promise<void> {
  const select = wrapper.find('[data-test="categoria-insumo-select"]')
  await select.trigger('click')
  await flushOverlay()
  const item = [...document.querySelectorAll<HTMLElement>('.p-select-option')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`categoria option not found: "${label}"`)
  item.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
  await flushOverlay()
  await nextTick()
}

/** PrimeVue InputNumber commits the model on blur — type then blur like a user. */
async function setNumber(wrapper: VueWrapper, testId: string, value: string): Promise<void> {
  const input = wrapper.find(`[data-test="${testId}"] input`)
  await input.setValue(value)
  await input.trigger('blur')
  await nextTick()
}

afterEach(() => {
  ElMessage.closeAll()
})

describe('InsumoForm (MOD-4)', () => {
  it('renders the six master fields and the categoria options in create mode', async () => {
    const wrapper = await mountForm('create')

    const text = wrapper.text()
    expect(text).toContain('Nombre del insumo')
    expect(text).toContain('Categoría')
    expect(text).toContain('Unidad de medida')
    expect(text).toContain('Stock actual')
    expect(text).toContain('Stock mínimo')
    expect(text).toContain('Costo promedio')

    await wrapper.find('[data-test="categoria-insumo-select"]').trigger('click')
    await flushOverlay()
    const options = [...document.querySelectorAll<HTMLElement>('.p-select-option')]
    expect(options.map((o) => o.textContent?.trim())).toEqual(['Granos', 'Abarrotes'])
  })

  it('blocks create submission with an empty nombre', async () => {
    const wrapper = await mountForm('create')

    await pickCategoria(wrapper, 'Granos')
    await wrapper.find('[data-test="unidad-insumo-input"]').setValue('kg')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe el nombre del insumo')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create submission without a categoria', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-insumo-input"]').setValue('Sal')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona la categoría')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create submission with an empty unidad de medida', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-insumo-input"]').setValue('Sal')
    await pickCategoria(wrapper, 'Granos')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe la unidad de medida')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact create payload', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-insumo-input"]').setValue('Harina de maíz')
    await pickCategoria(wrapper, 'Granos')
    await wrapper.find('[data-test="unidad-insumo-input"]').setValue('kg')
    await setNumber(wrapper, 'stock-actual-input', '10')
    await setNumber(wrapper, 'stock-minimo-input', '5')
    await setNumber(wrapper, 'costo-promedio-input', '3200')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      categoria_id: 1,
      nombre: 'Harina de maíz',
      unidad_medida: 'kg',
      stock_actual: 10,
      stock_minimo: 5,
      costo_promedio_actual: 3200,
    })
  })

  it('edit mode prefills every field from the row and emits the exact update payload', async () => {
    const wrapper = await mountForm('edit', INSUMO)

    // Every field prefills from the row: the name is an input VALUE (not text
    // content — wrapper.text() cannot see it), the categoria select renders
    // its label, and the number fields carry the parsed Decimal values.
    expect((wrapper.find('[data-test="nombre-insumo-input"]').element as HTMLInputElement).value).toBe(
      'Harina de maíz',
    )
    expect(wrapper.find('[data-test="nombre-insumo-input"]').exists()).toBe(true) // editable in edit mode
    expect(wrapper.text()).toContain('Granos') // categoria select prefilled

    await wrapper.find('[data-test="nombre-insumo-input"]').setValue('Harina de maíz premium')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      categoria_id: 1,
      nombre: 'Harina de maíz premium',
      unidad_medida: 'kg',
      stock_actual: 12,
      stock_minimo: 5,
      costo_promedio_actual: 2500,
    })
  })
})
