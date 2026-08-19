/**
 * MovimientosForm component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL MovimientosForm with PrimeVue and drives it through
 * real interaction (Select dropdowns, InputNumber fields):
 *  - client gates: missing tipo / empty descripcion / monto <= 0 each block
 *    submission with a warning and emit nothing
 *  - the socio select is OPTIONAL for every tipo (the backend does not
 *    require socio_id even for Retiro — verified backend service)
 *  - a valid form emits the exact MovimientoCreate POST body, omitting
 *    socio_id when unset and including it when a socio is picked
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import { clearToastHost, mountToastHost } from '../helpers/toast-host'
import esCO from '@/utils/locales/es-CO'
import MovimientosForm from '@/components/finanzas/MovimientosForm.vue'
import type { components } from '@/types/api.d'

type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']

const SOCIOS: SocioConfiguracionRead[] = [
  { id: 1, nombre: 'Ana María', porcentaje_participacion: '60.00' },
  { id: 2, nombre: 'Carlos Ruiz', porcentaje_participacion: '40.00' },
]

async function mountForm(saving = false): Promise<VueWrapper> {
  const wrapper = mount(MovimientosForm, {
    props: { socios: SOCIOS, saving },
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

mountToastHost()

afterEach(() => {
  clearToastHost()
})

describe('MovimientosForm (MOD-3 create)', () => {
  it('renders tipo/descripcion/monto/socio fields with the three tipo options', async () => {
    const wrapper = await mountForm()

    const text = wrapper.text()
    expect(text).toContain('Tipo de movimiento')
    expect(text).toContain('Descripción')
    expect(text).toContain('Monto')
    expect(text).toContain('Socio (opcional)')

    await pickOption(wrapper.find('[data-test="tipo-movimiento-select"]'), 'Retiro')
    expect(wrapper.find('[data-test="tipo-movimiento-select"]').text()).toContain('Retiro')
  })

  it('blocks submission without a tipo', async () => {
    const wrapper = await mountForm()

    await wrapper.find('[data-test="descripcion-input"]').setValue('Compra de arepas')
    await setNumber(wrapper, 'monto-input', '50000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona el tipo de movimiento')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks submission with an empty descripcion', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="tipo-movimiento-select"]'), 'Gasto')
    await setNumber(wrapper, 'monto-input', '50000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe una descripción')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks submission when monto is empty (InputNumber min 0.01 already clamps zero)', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="tipo-movimiento-select"]'), 'Gasto')
    await wrapper.find('[data-test="descripcion-input"]').setValue('Compra de arepas')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('El monto debe ser mayor a cero')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact payload without socio_id when no socio is picked (all tipos)', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="tipo-movimiento-select"]'), 'Retiro')
    await wrapper.find('[data-test="descripcion-input"]').setValue('Retiro manual')
    await setNumber(wrapper, 'monto-input', '150000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      tipo: 'Retiro',
      descripcion: 'Retiro manual',
      monto: 150000,
    })
  })

  it('includes socio_id in the payload when a socio is selected', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="tipo-movimiento-select"]'), 'Gasto')
    await pickOption(wrapper.find('[data-test="socio-select"]'), 'Ana María')
    await wrapper.find('[data-test="descripcion-input"]').setValue('Gasto a socio')
    await setNumber(wrapper, 'monto-input', '80000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      tipo: 'Gasto',
      descripcion: 'Gasto a socio',
      monto: 80000,
      socio_id: 1,
    })
  })
})

describe('MovimientosForm (T9 edit mode)', () => {
  const INITIAL: components['schemas']['MovimientoRead'] = {
    id: 7,
    fecha: '2026-08-01T10:00:00Z',
    tipo: 'Gasto',
    descripcion: 'Compra de arepas',
    monto: '50000.00',
    socio_id: 1,
    estado: 'activo',
    liquidacion_id: null,
  }

  const LIQUIDACION: components['schemas']['MovimientoRead'] = {
    id: 8,
    fecha: '2026-08-03T15:00:00Z',
    tipo: 'Retiro',
    descripcion: 'Liquidación abc',
    monto: '30000.00',
    socio_id: 1,
    estado: 'activo',
    liquidacion_id: 'abc00',
  }

  async function mountEdit(initial: components['schemas']['MovimientoRead']): Promise<VueWrapper> {
    const wrapper = mount(MovimientosForm, {
      props: { mode: 'edit', initial, socios: SOCIOS, saving: false },
      global: {
        plugins: [
          [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
        ],
      },
    })
    await nextTick()
    return wrapper
  }

  it('prefills every editable field from `initial` (watch prefill, same pattern as SociosForm)', async () => {
    const wrapper = await mountEdit(INITIAL)

    expect((wrapper.find('[data-test="descripcion-input"]').element as HTMLInputElement).value).toBe('Compra de arepas')
    // InputNumber renders the prefilled amount with the configured precision (2).
    expect((wrapper.find('[data-test="monto-input"] input').element as HTMLInputElement).value).toBe('50000.00')
    expect(wrapper.find('[data-test="socio-select"]').text()).toContain('Ana María')
    expect(wrapper.find('[data-test="tipo-movimiento-select"]').text()).toContain('Gasto')
    // The Fecha field is prefilled with the row's date (normalized, no 'Z').
    // The PrimeVue DatePicker model is a Date built from the "YYYY-MM-DDTHH:mm:ss" string.
    const fechaModel = wrapper.findComponent({ name: 'DatePicker' }).props('modelValue') as Date
    expect(fechaModel.toISOString()).toBe('2026-08-01T10:00:00.000Z')
  })

  it('emits the MovimientoUpdate payload on submit in edit mode', async () => {
    const wrapper = await mountEdit(INITIAL)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      fecha: '2026-08-01T10:00:00',
      tipo: 'Gasto',
      descripcion: 'Compra de arepas',
      monto: 50000,
      socio_id: 1,
    })
  })

  it('disables monto and socio for liquidacion rows (UI reinforcement; server is backstop)', async () => {
    const wrapper = await mountEdit(LIQUIDACION)

    expect(wrapper.find('[data-test="monto-input"] input').attributes('disabled')).toBeDefined()
    // PrimeVue Select renders a non-editable span when disabled (no inner input);
    // the root carries the p-disabled class and the combobox the aria-disabled attr.
    expect(wrapper.find('[data-test="socio-select"]').classes()).toContain('p-disabled')
    expect(wrapper.find('[data-test="socio-select"] [role="combobox"]').attributes('aria-disabled')).toBeDefined()
  })

  it('omits monto/socio_id from the edit payload for liquidacion rows (FIN-2)', async () => {
    const wrapper = await mountEdit(LIQUIDACION)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      fecha: '2026-08-03T15:00:00',
      tipo: 'Retiro',
      descripcion: 'Liquidación abc',
    })
  })
})