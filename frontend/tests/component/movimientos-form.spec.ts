/**
 * MovimientosForm component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL MovimientosForm with Element Plus and drives it through
 * real interaction (el-select dropdowns, el-input-number fields):
 *  - client gates: missing tipo / empty descripcion / monto <= 0 each block
 *    submission with a warning and emit nothing
 *  - the socio select is OPTIONAL for every tipo (the backend does not
 *    require socio_id even for Retiro — verified backend service)
 *  - a valid form emits the exact MovimientoCreate POST body, omitting
 *    socio_id when unset and including it when a socio is picked
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

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
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

/** Open an el-select by its data-test and click the option with the label. */
async function pickOption(select: ReturnType<VueWrapper['find']>, label: string): Promise<void> {
  await select.trigger('click')
  await nextTick()
  const item = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`dropdown option not found: "${label}"`)
  item.click()
  await flushPromises()
  await nextTick()
}

afterEach(() => {
  ElMessage.closeAll()
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
    await wrapper.find('[data-test="monto-input"] input').setValue('50000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona el tipo de movimiento')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks submission with an empty descripcion', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="tipo-movimiento-select"]'), 'Gasto')
    await wrapper.find('[data-test="monto-input"] input').setValue('50000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe una descripción')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks submission when monto is empty (el-input-number min 0.01 already clamps zero)', async () => {
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
    await wrapper.find('[data-test="monto-input"] input').setValue('150000')
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
    await wrapper.find('[data-test="monto-input"] input').setValue('80000')
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
