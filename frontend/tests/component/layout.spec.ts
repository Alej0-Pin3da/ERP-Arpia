/**
 * Layout shell component tests (task 1.7, spec SHELL-5; S0-T7 pilot, MIG-4).
 *
 * Mounts the REAL AppLayout + SidebarMenu + auth store + router guard
 * against a mocked HTTP layer (jsdom): the persistent shell an
 * authenticated user experiences — header with nombre/rol, a role-aware
 * sidebar (Usuarios hidden for operador/consulta), active-route
 * highlighting, and logout that clears the session and returns to /login.
 *
 * Slice-0 pilot (S0-T7): proves per-component PrimeVue imports (Tag/Button in
 * AppLayout), Teleported Toast/ConfirmDialog hosts (attachTo: document.body),
 * and hybrid dual-registration — ElementPlus plugin stays registered ONLY for
 * the el-menu assertions until S3-T4 replaces SidebarMenu.
 */
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from '@/App.vue'
import { createAppRouter } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/endpoints'
import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'

vi.mock('@/api/endpoints', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}))

// The layout renders the active route through <router-view>; the module
// views land in later PRs, so stub the placeholder they resolve to.
vi.mock('@/views/RoutePlaceholder.vue', () => ({
  default: { name: 'RoutePlaceholderStub', template: '<div />' },
}))

const OPERADOR = { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol: 'operador' }

/**
 * Mount the real app root with an already-authenticated store of the given
 * role: App -> router-view -> AppLayout (the shell under test) ->
 * router-view -> active route. Mounting the shell directly would double it,
 * because the active route (/dashboard) resolves to AppLayout itself.
 *
 * attachTo: document.body — App.vue mounts Toast/ConfirmDialog hosts which
 * Teleport to <body>; without an attached root the teleported hosts are
 * dropped. ElementPlus stays registered for el-menu until S3 (MIG-4 pilot);
 * PrimeVue + services mirror main.ts dual registration.
 */
async function mountLayout(rol: string) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { ...OPERADOR, rol },
  })
  const router = createAppRouter(createMemoryHistory())
  const wrapper = mount(App, {
    attachTo: document.body,
    global: {
      plugins: [
        pinia,
        router,
        ElementPlus,
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
        ToastService,
        ConfirmationService,
      ],
    },
  })
  await router.isReady()
  await flushPromises()
  return { wrapper, router, auth }
}

function sidebarLabels(wrapper: ReturnType<typeof mount>): string[] {
  return wrapper.findAll('.el-menu-item').map((item) => item.text())
}

describe('AppLayout (spec SHELL-5)', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows the user nombre and rol in the header', async () => {
    const { wrapper } = await mountLayout('operador')

    expect(wrapper.text()).toContain('Pepe Operador')
    expect(wrapper.text()).toContain('Operador')
  })

  it('shows the human role label for an admin in the header', async () => {
    const { wrapper } = await mountLayout('admin')

    expect(wrapper.text()).toContain('Administrador')
  })

  it('renders the role badge as a per-component PrimeVue Tag (S0-T7 pilot)', async () => {
    const { wrapper } = await mountLayout('operador')

    const badge = wrapper.find('.p-tag')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('Operador')
  })

  it('renders the logout control as a per-component PrimeVue Button (S0-T7 pilot)', async () => {
    const { wrapper } = await mountLayout('operador')

    const logout = wrapper.find('.p-button')
    expect(logout.exists()).toBe(true)
    expect(logout.text()).toContain('Cerrar sesión')
  })

  it('renders every section including Usuarios for an admin', async () => {
    const { wrapper } = await mountLayout('admin')

    const labels = sidebarLabels(wrapper)
    expect(labels).toHaveLength(10)
    expect(labels).toContain('Usuarios')
    expect(labels).toContain('Omisiones')
    expect(labels).toEqual([
      'Dashboard',
      'Análisis',
      'Ventas',
      'Devoluciones',
      'Finanzas',
      'Inventario',
      'Productos',
      'Maestros',
      'Omisiones',
      'Usuarios',
    ])
  })

  it('hides the admin-only Usuarios entry for an operador', async () => {
    const { wrapper } = await mountLayout('operador')

    const labels = sidebarLabels(wrapper)
    expect(labels).toHaveLength(9)
    expect(labels).not.toContain('Usuarios')
    expect(labels).toContain('Ventas')
    expect(labels).toContain('Dashboard')
    expect(labels).toContain('Análisis')
    expect(labels).toContain('Omisiones')
  })

  it('hides the admin-only Usuarios entry for a consulta', async () => {
    const { wrapper } = await mountLayout('consulta')

    const labels = sidebarLabels(wrapper)
    expect(labels).toHaveLength(9)
    expect(labels).not.toContain('Usuarios')
    expect(labels).toContain('Análisis')
    expect(labels).toContain('Omisiones')
  })

  it('highlights the active route and navigates from the sidebar', async () => {
    const { wrapper, router } = await mountLayout('operador')

    // Mounted at /dashboard (root redirect) — the Dashboard item is active.
    expect(wrapper.find('.el-menu-item.is-active').text()).toBe('Dashboard')

    const ventasItem = wrapper.findAll('.el-menu-item').find((item) => item.text() === 'Ventas')
    await ventasItem!.trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/ventas')
    expect(wrapper.find('.el-menu-item.is-active').text()).toBe('Ventas')
  })

  it('logs out: invalidates the refresh token, clears the session and returns to /login', async () => {
    const { wrapper, router, auth } = await mountLayout('admin')

    const logoutButton = wrapper.findAll('button').find((b) => b.text() === 'Cerrar sesión')
    expect(logoutButton).toBeDefined()

    await logoutButton!.trigger('click')
    await flushPromises()

    expect(authApi.logout).toHaveBeenCalledWith({ refresh_token: 'ref-1' })
    expect(auth.isAuthenticated).toBe(false)
    expect(router.currentRoute.value.path).toBe('/login')
  })
})