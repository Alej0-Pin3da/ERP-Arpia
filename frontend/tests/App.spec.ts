import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { defineComponent, h } from 'vue'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import { describe, expect, it } from 'vitest'

import App from '@/App.vue'
import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import ConfirmDialog from 'primevue/confirmdialog'

const primeVuePlugins = [
  [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
  ToastService,
  ConfirmationService,
]

describe('App', () => {
  it('renders the active route through the router outlet', async () => {
    const Dummy = defineComponent({ name: 'DummyRoute', render: () => h('div', 'dummy route content') })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: Dummy }],
    })

    const wrapper = mount(App, {
      attachTo: document.body,
      global: { plugins: [router, ...primeVuePlugins] },
    })
    await router.isReady()
    await flushPromises()

    // The SPA shell delegates rendering to <router-view>.
    expect(wrapper.text()).toContain('dummy route content')
  })

  it('mounts the Toast and ConfirmDialog hosts (design D4)', async () => {
    const Dummy = defineComponent({ name: 'DummyRoute', render: () => h('div', 'dummy route content') })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: Dummy }],
    })

    const wrapper = mount(App, {
      attachTo: document.body,
      global: { plugins: [router, ...primeVuePlugins] },
    })
    await router.isReady()
    await flushPromises()

    // Toast always renders its container and Teleports it to <body>.
    expect(document.body.querySelector('.p-toast')).not.toBeNull()
    // ConfirmDialog wraps a Dialog with visible=false until a confirmation is
    // required (S4 confirm.ts), so assert the host component is mounted.
    expect(wrapper.findComponent(ConfirmDialog).exists()).toBe(true)
    // The route outlet keeps rendering alongside the hosts.
    expect(wrapper.text()).toContain('dummy route content')
  })
})