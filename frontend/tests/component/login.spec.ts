/**
 * LoginView component tests (task 1.8, spec SHELL-3).
 *
 * Mounts the REAL view + real auth store + real router guard against a
 * mocked HTTP layer and jsdom localStorage — the full login journey a user
 * experiences: fill form -> submit -> navigate to /dashboard, or a 401
 * surfaced inline as "incorrect credentials".
 */
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LoginView from '@/views/LoginView.vue'
import { createAppRouter } from '@/router'
import { authApi } from '@/api/endpoints'

const TOKEN = {
  access_token: 'acc-1',
  refresh_token: 'ref-1',
  token_type: 'bearer',
  rol: 'admin',
} as const

const ANA = { id: 1, nombre: 'Ana Admin', email: 'ana@arpia.com.co', rol: 'admin' }

function unauthorizedError() {
  const err = new Error('Request failed with status code 401') as Error & {
    response?: { status: number }
  }
  err.response = { status: 401 }
  return err
}

vi.mock('@/api/endpoints', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}))

async function mountLoginView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createAppRouter(createMemoryHistory())
  // Mounting installs the router, which starts the initial navigation.
  const wrapper = mount(LoginView, { global: { plugins: [pinia, router, ElementPlus] } })
  await router.isReady()
  return { wrapper, router }
}

describe('LoginView (spec SHELL-3)', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.clearAllMocks()
  })

  it('logs in with valid credentials, persists tokens and navigates to /dashboard', async () => {
    vi.mocked(authApi.login).mockResolvedValue(TOKEN)
    vi.mocked(authApi.me).mockResolvedValue(ANA)
    const { wrapper, router } = await mountLoginView()

    await wrapper.find('input[type="email"]').setValue('ana@arpia.com.co')
    await wrapper.find('input[type="password"]').setValue('supersecret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(authApi.login).toHaveBeenCalledWith({
      email: 'ana@arpia.com.co',
      password: 'supersecret',
    })
    // Real jsdom localStorage receives the token pair + user.
    expect(window.localStorage.getItem('arpia_access')).toBe('acc-1')
    expect(window.localStorage.getItem('arpia_refresh')).toBe('ref-1')
    expect(window.localStorage.getItem('arpia_user')).toContain('Ana Admin')
    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('surfaces a 401 as an incorrect-credentials message without navigating', async () => {
    vi.mocked(authApi.login).mockRejectedValue(unauthorizedError())
    const { wrapper, router } = await mountLoginView()

    await wrapper.find('input[type="email"]').setValue('ana@arpia.com.co')
    await wrapper.find('input[type="password"]').setValue('wrong-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Correo o contraseña incorrectos')
    expect(router.currentRoute.value.path).not.toBe('/dashboard')
    expect(window.localStorage.getItem('arpia_access')).toBeNull()
  })

  it('honors the redirect query after a successful login', async () => {
    vi.mocked(authApi.login).mockResolvedValue(TOKEN)
    vi.mocked(authApi.me).mockResolvedValue(ANA)
    const { wrapper, router } = await mountLoginView()
    // Simulate an unauthenticated user bounced to /login?redirect=/usuarios.
    await router.replace({ name: 'login', query: { redirect: '/usuarios' } })

    await wrapper.find('input[type="email"]').setValue('ana@arpia.com.co')
    await wrapper.find('input[type="password"]').setValue('supersecret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/usuarios')
  })
})
