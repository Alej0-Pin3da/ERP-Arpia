/**
 * Router guard tests (task 1.6, spec SHELL-4).
 *
 * The REAL router + global guard from `@/router` run against a memory
 * history, and the auth store is real too — only the HTTP/storage layer is
 * mocked. This exercises the restore-before-role-check race for real
 * (design learning #5): if the guard evaluated `meta.roles` before
 * `restoreIfNeeded()` resolved, the role would be null and every protected
 * route would bounce to /dashboard.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, type Router } from 'vue-router'

import { createAppRouter } from '@/router'
import { authApi } from '@/api/endpoints'

// --- module mocks -----------------------------------------------------------

const storageState = {
  accessToken: null as string | null,
  refreshToken: null as string | null,
  user: null as unknown,
}

vi.mock('@/api/storage', () => ({
  STORAGE_KEYS: { access: 'arpia_access', refresh: 'arpia_refresh', user: 'arpia_user' },
  readAccessToken: () => storageState.accessToken,
  readRefreshToken: () => storageState.refreshToken,
  readUser: () => storageState.user,
  writeTokens: (access: string, refresh: string) => {
    storageState.accessToken = access
    storageState.refreshToken = refresh
  },
  writeUser: (user: unknown) => {
    storageState.user = user
  },
  clearSession: () => {
    storageState.accessToken = null
    storageState.refreshToken = null
    storageState.user = null
  },
}))

vi.mock('@/api/endpoints', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}))

// Views are rendered by the router AFTER the guard; stub them so this spec
// asserts navigation behavior, not view content.
vi.mock('@/views/LoginView.vue', () => ({ default: { name: 'LoginViewStub' } }))
vi.mock('@/views/RoutePlaceholder.vue', () => ({ default: { name: 'RoutePlaceholderStub' } }))

// --- fixtures ---------------------------------------------------------------

const ADMIN = { id: 1, nombre: 'Ana Admin', email: 'ana@arpia.com.co', rol: 'admin' }
const OPERADOR = { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol: 'operador' }

async function makeRouter(): Promise<Router> {
  const router = createAppRouter(createMemoryHistory())
  // Kick off the initial navigation (a memory router only navigates once
  // pushed/installed), then settle it before the assertions run.
  await router.push('/')
  return router
}

describe('router guards (spec SHELL-4)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    storageState.accessToken = null
    storageState.refreshToken = null
    storageState.user = null
    vi.clearAllMocks()
  })

  it('redirects unauthenticated navigation to /login with a redirect query', async () => {
    const router = await makeRouter()

    await router.push('/dashboard')

    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/dashboard')
  })

  it('keeps the public /login route reachable without a session', async () => {
    const router = await makeRouter()

    await router.push('/login')

    expect(router.currentRoute.value.path).toBe('/login')
    expect(authApi.me).not.toHaveBeenCalled()
  })

  it('restores the session BEFORE evaluating meta.roles (no role-guard race)', async () => {
    storageState.accessToken = 'acc-1'
    storageState.refreshToken = 'ref-1'
    vi.mocked(authApi.me).mockResolvedValue(ADMIN)
    const router = await makeRouter()

    await router.push('/usuarios')

    // If roles had been checked before restore, role would be null and the
    // guard would have bounced to /dashboard. Admin lands on /usuarios.
    expect(router.currentRoute.value.path).toBe('/usuarios')
    expect(authApi.me).toHaveBeenCalledTimes(1)
  })

  it('blocks an operador from the admin-only /usuarios route', async () => {
    storageState.accessToken = 'acc-1'
    vi.mocked(authApi.me).mockResolvedValue(OPERADOR)
    const router = await makeRouter()

    await router.push('/usuarios')

    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('allows an operador into operational routes such as /ventas', async () => {
    storageState.accessToken = 'acc-1'
    vi.mocked(authApi.me).mockResolvedValue(OPERADOR)
    const router = await makeRouter()

    await router.push('/ventas')

    expect(router.currentRoute.value.path).toBe('/ventas')
  })

  it('redirects the root path to /dashboard for an authenticated session', async () => {
    storageState.accessToken = 'acc-1'
    vi.mocked(authApi.me).mockResolvedValue(ADMIN)
    const router = await makeRouter()

    await router.push('/')

    expect(router.currentRoute.value.path).toBe('/dashboard')
  })
})
