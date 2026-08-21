import { mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { describe, expect, it } from 'vitest'

import ErrorState from '@/components/common/ErrorState.vue'
import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'

function mountError(props: Record<string, unknown> = {}) {
  return mount(ErrorState, {
    props: { message: 'Error de carga', ...props },
    global: {
      plugins: [[PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }]],
    },
  })
}

describe('ErrorState', () => {
  it('renders message', () => {
    const wrapper = mountError({ message: 'No se pudo cargar' })
    expect(wrapper.find('[data-test="error-message"]').text()).toContain('No se pudo cargar')
  })

  it('renders retry button and emits retry', async () => {
    const wrapper = mountError({ message: 'Fallo' })
    const btn = wrapper.find('[data-test="error-retry"]')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    expect(wrapper.emitted('retry')).toBeDefined()
  })

  it('has data-test container', () => {
    const wrapper = mountError()
    expect(wrapper.find('[data-test="error-state"]').exists()).toBe(true)
  })
})
