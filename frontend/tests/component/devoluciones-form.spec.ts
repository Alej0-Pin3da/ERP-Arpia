/**
 * Devoluciones create form component tests (task 2.3, spec MOD-2).
 *
 * Mounts the REAL DevolucionesForm with PrimeVue and drives it
 * through real interaction. The CRITICAL behavior (spec MOD-2):
 *  - tipo 'total'  -> items section HIDDEN; a submit without items is valid
 *    (POST returns 201) and the payload has NO items key
 *  - tipo 'parcial' -> items section REQUIRED (server 422 otherwise); the
 *    client blocks a parcial submit with no complete item and emits nothing
 *  - venta_id is required — submit without it is blocked client-side
 *  - precio_unitario rides in the payload (schema-required) but is never
 *    trusted server-side (snapshot pricing)
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import DevolucionesForm from '@/components/devoluciones/DevolucionesForm.vue'
import type { components } from '@/types/api.d'

type ProductoRead = components['schemas']['ProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']

const PRODUCTOS: ProductoRead[] = [
  {
    id: 1,
    tipo_producto_id: 1,
    nombre: 'Arepa de huevo',
    requiere_fabricacion: true,
    costos_operativos_fijos: '0',
    precio_venta_sugerido: '5000',
  },
  {
    id: 2,
    tipo_producto_id: 1,
    nombre: 'Jugo de naranja',
    requiere_fabricacion: false,
    costos_operativos_fijos: '0',
    precio_venta_sugerido: '8000',
  },
]

const VARIANTES: VarianteProductoRead[] = [
  { id: 5, producto_id: 1, nombre_variante: 'Grande', precio_venta: '6000' },
]

const loadVariantes = vi.fn().mockResolvedValue(VARIANTES)

async function mountForm(saving = false): Promise<VueWrapper> {
  const wrapper = mount(DevolucionesForm, {
    props: { productos: PRODUCTOS, loadVariantes, saving },
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

/** Open a PrimeVue Select by its data-test and click the option with the label. */
async function pickOption(select: ReturnType<VueWrapper['find']>, label: string): Promise<void> {
  await select.trigger('click')
  await flushOverlay()
  const item = [...document.querySelectorAll<HTMLElement>('.p-select-option')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`dropdown option not found: "${label}"`)
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

/** Switch the tipo select to the given label (Total | Parcial). */
async function setTipo(wrapper: VueWrapper, label: string): Promise<void> {
  await pickOption(wrapper.find('[data-test="tipo-select"]'), label)
}

afterEach(() => {
  ElMessage.closeAll()
})

describe('DevolucionesForm (MOD-2 create)', () => {
  it('renders venta_id, tipo and motivo; items section is hidden for the default tipo total', async () => {
    const wrapper = await mountForm()

    const text = wrapper.text()
    expect(text).toContain('Número de venta')
    expect(text).toContain('Tipo de devolución')
    expect(text).toContain('Motivo')
    expect(wrapper.find('[data-test="tipo-select"]').text()).toContain('Total') // default
    // CRITICAL: a total return does NOT need items — no item rows render.
    expect(wrapper.findAll('[data-test="devolucion-item"]')).toHaveLength(0)

    // The tipo dropdown offers both types.
    await setTipo(wrapper, 'Parcial')
    expect(wrapper.find('[data-test="tipo-select"]').text()).toContain('Parcial')
  })

  it('shows the items section ONLY for tipo parcial and hides it again on total', async () => {
    const wrapper = await mountForm()
    expect(wrapper.findAll('[data-test="devolucion-item"]')).toHaveLength(0)

    await setTipo(wrapper, 'Parcial')
    expect(wrapper.findAll('[data-test="devolucion-item"]')).toHaveLength(1)

    await setTipo(wrapper, 'Total')
    expect(wrapper.findAll('[data-test="devolucion-item"]')).toHaveLength(0)
  })

  it('blocks submission without a venta id and emits nothing', async () => {
    const wrapper = await mountForm()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Indica el número de la venta')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('total tipo: submit WITHOUT items emits a payload with no items key', async () => {
    const wrapper = await mountForm()
    await setNumber(wrapper, 'venta-id-input', '9')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0]).toEqual({ venta_id: 9, tipo: 'total' })
  })

  it('total tipo: a non-empty motivo is included in the payload', async () => {
    const wrapper = await mountForm()
    await setNumber(wrapper, 'venta-id-input', '9')
    await wrapper.find('[data-test="motivo-input"]').setValue('Cliente pidió cancelación')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0]).toEqual({
      venta_id: 9,
      tipo: 'total',
      motivo: 'Cliente pidió cancelación',
    })
  })

  it('parcial tipo: blocks a submit with no complete item (server would 422)', async () => {
    const wrapper = await mountForm()
    await setTipo(wrapper, 'Parcial')
    await setNumber(wrapper, 'venta-id-input', '10')

    // Leave the default empty row untouched -> no valid item.
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('devolución parcial requiere')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('parcial tipo: emits the exact payload for a complete item', async () => {
    const wrapper = await mountForm()
    await setTipo(wrapper, 'Parcial')
    await setNumber(wrapper, 'venta-id-input', '10')

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo')
    // precio_unitario auto-defaults from precio_venta_sugerido (schema-required;
    // the server prices from the sale-time snapshot and ignores it).
    const precioInput = wrapper.find('[data-test="precio-input"] input')
    expect((precioInput.element as HTMLInputElement).value).toBe('5000')
    await pickOption(wrapper.find('[data-test="variante-select"]'), 'Grande')
    await setNumber(wrapper, 'cantidad-input', '2')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0]).toEqual({
      venta_id: 10,
      tipo: 'parcial',
      items: [{ producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 }],
    })
  })
})