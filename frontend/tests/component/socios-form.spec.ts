/**
 * SociosForm component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL SociosForm with PrimeVue in both modes:
 *  - create: nombre + porcentaje fields; empty nombre and empty porcentaje
 *    each block submission with a warning
 *  - edit: percentage only (the backend SocioConfiguracionUpdate schema has
 *    NO nombre — the partner name is not updatable)
 *  - a valid create emits the exact SocioConfiguracionCreate body; a valid
 *    edit emits the exact SocioConfiguracionUpdate body
 * The view owns the POST/PATCH, the 422 sum-to-100 surfacing and the refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import SociosForm from '@/components/finanzas/SociosForm.vue'
import type { components } from '@/types/api.d'

type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']

const SOCIO: SocioConfiguracionRead = { id: 1, nombre: 'Ana María', porcentaje_participacion: '60.00' }

async function mountForm(mode: 'create' | 'edit' = 'create', initial: SocioConfiguracionRead | null = null): Promise<VueWrapper> {
  const wrapper = mount(SociosForm, {
    props: { mode, initial },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  return wrapper
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

describe('SociosForm (MOD-3)', () => {
  it('renders nombre + porcentaje in create mode', async () => {
    const wrapper = await mountForm('create')

    const text = wrapper.text()
    expect(text).toContain('Nombre del socio')
    expect(text).toContain('Porcentaje de participación')
  })

  it('blocks create submission with an empty nombre', async () => {
    const wrapper = await mountForm('create')

    await setNumber(wrapper, 'porcentaje-socio-input', '25')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe el nombre del socio')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create submission with an empty porcentaje', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-socio-input"]').setValue('Luis Vega')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('El porcentaje debe ser mayor a cero')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact create payload', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-socio-input"]').setValue('Luis Vega')
    await setNumber(wrapper, 'porcentaje-socio-input', '25')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ nombre: 'Luis Vega', porcentaje_participacion: 25 })
  })

  it('edit mode shows the name read-only and edits the percentage only', async () => {
    const wrapper = await mountForm('edit', SOCIO)

    const text = wrapper.text()
    expect(text).toContain('Ana María')
    expect(wrapper.find('[data-test="nombre-socio-input"]').exists()).toBe(false)

    await setNumber(wrapper, 'porcentaje-socio-input', '20')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ porcentaje_participacion: 20 })
  })

  it('blocks edit submission when the percentage is cleared', async () => {
    const wrapper = await mountForm('edit', SOCIO)

    // Edit mode prefills the share from the row — the gate fires only after
    // the user clears the field (InputNumber empties to null on blur).
    const input = wrapper.find('[data-test="porcentaje-socio-input"] input')
    await input.setValue('')
    await input.trigger('blur')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('El porcentaje debe ser mayor a cero')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })
})