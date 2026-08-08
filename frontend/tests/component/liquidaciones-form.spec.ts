/**
 * LiquidacionesForm component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL LiquidacionesForm with Element Plus: the one-time
 * settlement warning is rendered, an empty monto blocks submission, and a
 * valid form emits the exact LiquidacionCreate POST body (notas omitted when
 * empty). The view owns the POST, the result table and the 409 replay
 * surfacing.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import LiquidacionesForm from '@/components/finanzas/LiquidacionesForm.vue'

async function mountForm(saving = false): Promise<VueWrapper> {
  const wrapper = mount(LiquidacionesForm, {
    props: { saving },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

afterEach(() => {
  ElMessage.closeAll()
})

describe('LiquidacionesForm (MOD-3)', () => {
  it('renders monto/notas fields and the one-time settlement warning', async () => {
    const wrapper = await mountForm()

    const text = wrapper.text()
    expect(text).toContain('Monto a liquidar')
    expect(text).toContain('Notas')
    expect(text).toContain('una sola vez') // one-time settlement warning
  })

  it('blocks submission when monto is empty', async () => {
    const wrapper = await mountForm()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Indica el monto a liquidar')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the payload without notas when notas is empty', async () => {
    const wrapper = await mountForm()

    await wrapper.find('[data-test="monto-liquidacion-input"] input').setValue('5000000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ monto: 5000000 })
  })

  it('emits the payload with notas when provided', async () => {
    const wrapper = await mountForm()

    await wrapper.find('[data-test="monto-liquidacion-input"] input').setValue('5000000')
    await wrapper.find('[data-test="notas-input"]').setValue('Utilidades agosto')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ monto: 5000000, notas: 'Utilidades agosto' })
  })
})
