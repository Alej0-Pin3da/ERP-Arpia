/**
 * Layout shell component tests (task 1.7, spec SHELL-5).
 *
 * Mounts the REAL AppLayout + SidebarMenu + auth store + router guard
 * against a mocked HTTP layer (jsdom): the persistent shell an
 * authenticated user experiences — header with nombre/rol, a role-aware
 * sidebar (Usuarios hidden for operador/consulta), active-route
 * highlighting, and logout that clears the session and returns to /login.
 */
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from '@/App.vue'
import { createAppRouter } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/endpoints'

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
  const wrapper = mount(App, { global: { plugins: [pinia, router, ElementPlus] } })
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

  it('renders every section including Usuarios for an admin', async () => {
    const { wrapper } = await mountLayout('admin')

    const labels = sidebarLabels(wrapper)
    expect(labels).toHaveLength(9)
    expect(labels).toContain('Usuarios')
    expect(labels).toContain('Omisiones')
    expect(labels).toEqual([
      'Dashboard',
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
    expect(labels).toHaveLength(8)
    expect(labels).not.toContain('Usuarios')
    expect(labels).toContain('Ventas')
    expect(labels).toContain('Dashboard')
    expect(labels).toContain('Omisiones')
  })

  it('hides the admin-only Usuarios entry for a consulta', async () => {
    const { wrapper } = await mountLayout('consulta')

    const labels = sidebarLabels(wrapper)
    expect(labels).toHaveLength(8)
    expect(labels).not.toContain('Usuarios')
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
