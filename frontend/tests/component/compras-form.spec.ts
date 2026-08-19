/**
 * ComprasForm component tests (PR9, spec MOD-4).
 *
 * Mounts the REAL ComprasForm with PrimeVue: insumo select fed by the
 * insumos catalog, cantidad and precio_unitario number fields, the WAC hint,
 * client gates (no insumo / empty cantidad / empty precio each block with a
 * warning), and the exact CompraInsumoCreate payload on a valid submit
 * (`cantidad_comprada` / `precio_unitario_compra` — the schema names).
 * The view owns the POST (WAC runs server-side) and the two-tab refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import ComprasForm from '@/components/inventario/ComprasForm.vue'
import type { components } from '@/types/api.d'

type InsumoRead = components['schemas']['InsumoRead']

const INSUMOS: InsumoRead[] = [
  {
    id: 2,
    categoria_id: 1,
    nombre: 'Harina de maíz',
    unidad_medida: 'kg',
    stock_actual: '12.00',
    stock_minimo: '5.00',
    costo_promedio_actual: '2500.00',
    nombre_categoria: 'Granos',
  },
  {
    id: 3,
    categoria_id: 2,
    nombre: 'Aceite',
    unidad_medida: 'L',
    stock_actual: '8.00',
    stock_minimo: '3.00',
    costo_promedio_actual: '9800.00',
    nombre_categoria: 'Abarrotes',
  },
]

async function mountForm(saving = false): Promise<VueWrapper> {
  const wrapper = mount(ComprasForm, {
    props: { insumos: INSUMOS, saving },
    global: {
      plugins: [
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

async function pickInsumo(wrapper: VueWrapper, label: string): Promise<void> {
  const select = wrapper.find('[data-test="compra-insumo-select"]')
  await select.trigger('click')
  await flushOverlay()
  const item = [...document.querySelectorAll<HTMLElement>('.p-select-option')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`insumo option not found: "${label}"`)
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

describe('ComprasForm (MOD-4)', () => {
  it('renders the insumo select with the catalog options and the WAC hint', async () => {
    const wrapper = await mountForm()

    const text = wrapper.text()
    expect(text).toContain('Insumo')
    expect(text).toContain('Cantidad')
    expect(text).toContain('Precio unitario')
    expect(text).toContain('stock') // WAC hint mentions the stock/cost update

    await wrapper.find('[data-test="compra-insumo-select"]').trigger('click')
    await flushOverlay()
    const options = [...document.querySelectorAll<HTMLElement>('.p-select-option')]
    expect(options.map((o) => o.textContent?.trim())).toEqual(['Harina de maíz', 'Aceite'])
  })

  it('blocks submission without an insumo', async () => {
    const wrapper = await mountForm()

    await setNumber(wrapper, 'compra-cantidad-input', '3')
    await setNumber(wrapper, 'compra-precio-input', '2500')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona el insumo')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks submission with an empty cantidad', async () => {
    const wrapper = await mountForm()

    await pickInsumo(wrapper, 'Harina de maíz')
    await setNumber(wrapper, 'compra-precio-input', '2500')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('La cantidad debe ser mayor a cero')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks submission with an empty precio unitario', async () => {
    const wrapper = await mountForm()

    await pickInsumo(wrapper, 'Harina de maíz')
    await setNumber(wrapper, 'compra-cantidad-input', '3')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Indica el precio unitario')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact CompraInsumoCreate payload', async () => {
    const wrapper = await mountForm()

    await pickInsumo(wrapper, 'Harina de maíz')
    await setNumber(wrapper, 'compra-cantidad-input', '2.5')
    await setNumber(wrapper, 'compra-precio-input', '4500')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      insumo_id: 2,
      cantidad_comprada: 2.5,
      precio_unitario_compra: 4500,
    })
  })
})