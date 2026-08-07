import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import App from '@/App.vue'

describe('App', () => {
  it('renders the scaffold shell with the app name', () => {
    const wrapper = mount(App)
    expect(wrapper.find('h1').text()).toBe('ERP Arpia')
  })
})
