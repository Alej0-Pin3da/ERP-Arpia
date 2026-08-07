import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { defineComponent, h } from 'vue'
import { describe, expect, it } from 'vitest'

import App from '@/App.vue'

describe('App', () => {
  it('renders the active route through the router outlet', async () => {
    const Dummy = defineComponent({ name: 'DummyRoute', render: () => h('div', 'dummy route content') })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: Dummy }],
    })

    const wrapper = mount(App, { global: { plugins: [router] } })
    await router.isReady()
    await flushPromises()

    // The SPA shell delegates rendering to <router-view>.
    expect(wrapper.text()).toContain('dummy route content')
  })
})
