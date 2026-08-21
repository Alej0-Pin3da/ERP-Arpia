import { mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { describe, expect, it } from 'vitest'

import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'

function mountSkeleton(props: Record<string, unknown> = {}) {
  return mount(LoadingSkeleton, {
    props: { ...props },
    global: {
      plugins: [[PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }]],
    },
  })
}

describe('LoadingSkeleton', () => {
  it('renders rows * columns skeleton cells with defaults', () => {
    const wrapper = mountSkeleton()
    // defaults: rows 5, columns 4 => 20 cells
    expect(wrapper.findAll('[data-test="skeleton-row"]')).toHaveLength(5)
    expect(wrapper.findAll('[data-test="skeleton-cell"]')).toHaveLength(20)
  })

  it('respects rows and columns props', () => {
    const wrapper = mountSkeleton({ rows: 2, columns: 3 })
    expect(wrapper.findAll('[data-test="skeleton-row"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="skeleton-cell"]')).toHaveLength(6)
  })

  it('renders container with test id', () => {
    const wrapper = mountSkeleton({ rows: 1, columns: 1 })
    expect(wrapper.find('[data-test="loading-skeleton"]').exists()).toBe(true)
  })
})
