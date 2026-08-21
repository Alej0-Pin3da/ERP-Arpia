import { mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { describe, expect, it } from 'vitest'

import EmptyState from '@/components/common/EmptyState.vue'
import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'

function mountEmpty(props: Record<string, unknown> = {}) {
  return mount(EmptyState, {
    props: { title: 'Sin datos', ...props },
    global: {
      plugins: [[PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }]],
    },
  })
}

describe('EmptyState', () => {
  it('renders icon, title and description', () => {
    const wrapper = mountEmpty({ icon: 'pi pi-inbox', title: 'Sin insumos', description: 'No hay datos' })
    expect(wrapper.find('[data-test="empty-icon"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="empty-icon"]').classes()).toContain('pi-inbox')
    expect(wrapper.find('[data-test="empty-title"]').text()).toBe('Sin insumos')
    expect(wrapper.find('[data-test="empty-description"]').text()).toBe('No hay datos')
  })

  it('hides description when not provided', () => {
    const wrapper = mountEmpty({ title: 'Vacío' })
    expect(wrapper.find('[data-test="empty-description"]').exists()).toBe(false)
  })

  it('renders action button when actionLabel is provided and emits action', async () => {
    const wrapper = mountEmpty({ title: 'Vacío', actionLabel: 'Recargar' })
    const btn = wrapper.find('[data-test="empty-action"]')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    expect(wrapper.emitted('action')).toBeDefined()
  })

  it('hides action button when no actionLabel', () => {
    const wrapper = mountEmpty({ title: 'Vacío' })
    expect(wrapper.find('[data-test="empty-action"]').exists()).toBe(false)
  })

  it('uses default icon when none provided', () => {
    const wrapper = mountEmpty({ title: 'Vacío' })
    expect(wrapper.find('[data-test="empty-icon"]').classes().join(' ')).toContain('pi-inbox')
  })
})
