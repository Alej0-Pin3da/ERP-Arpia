/**
 * Auth store tests (task 1.5, spec SHELL-3).
 *
 * The store is driven against MOCKED api/storage/refresh modules — the HTTP
 * layer is already covered by refresh.spec.ts. These tests prove the
 * user-visible session contract:
 *   - login persists tokens + authoritative user, rethrows on failure
 *   - restoreIfNeeded reconciles /auth/me on reload, rotating via the
 *     single-flight refresh when the access token is expired (401)
 *   - logout POSTs the refresh token and clears storage + state
 *   - getters expose isAuthenticated / role / userName
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/endpoints'
import { refreshSession } from '@/api/refresh'

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

vi.mock('@/api/refresh', () => ({
  refreshSession: vi.fn(),
}))

// --- fixtures ---------------------------------------------------------------

const TOKEN = {
  access_token: 'acc-1',
  refresh_token: 'ref-1',
  token_type: 'bearer',
  rol: 'admin',
} as const

const ROTATED = {
  access_token: 'acc-2',
  refresh_token: 'ref-2',
  token_type: 'bearer',
  rol: 'admin',
} as const

const ANA = { id: 1, nombre: 'Ana Admin', email: 'ana@arpia.com.co', rol: 'admin' }

/** Axios-shaped 401 error (as thrown by the mocked HTTP layer). */
function unauthorizedError() {
  const err = new Error('Request failed with status code 401') as Error & {
    response?: { status: number }
  }
  err.response = { status: 401 }
  return err
}

describe('auth store (spec SHELL-3)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    storageState.accessToken = null
    storageState.refreshToken = null
    storageState.user = null
    vi.clearAllMocks()
  })

  it('login persists tokens and the authoritative user, then exposes them', async () => {
    vi.mocked(authApi.login).mockResolvedValue(TOKEN)
    vi.mocked(authApi.me).mockResolvedValue(ANA)

    const store = useAuthStore()
    await store.login('ana@arpia.com.co', 'supersecret')

    expect(store.accessToken).toBe('acc-1')
    expect(store.refreshToken).toBe('ref-1')
    expect(store.user).toEqual(ANA)
    expect(store.role).toBe('admin')
    expect(store.isAuthenticated).toBe(true)
    // Persisted to localStorage through the storage module.
    expect(storageState.accessToken).toBe('acc-1')
    expect(storageState.refreshToken).toBe('ref-1')
    expect(storageState.user).toEqual(ANA)
  })

  it('login rethrows on bad credentials and leaves the session empty', async () => {
    vi.mocked(authApi.login).mockRejectedValue(unauthorizedError())

    const store = useAuthStore()
    await expect(store.login('ana@arpia.com.co', 'wrong')).rejects.toThrow()

    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(storageState.accessToken).toBeNull()
    expect(vi.mocked(authApi.me)).not.toHaveBeenCalled()
  })

  it('refresh rotates the in-memory tokens via the single-flight call', async () => {
    vi.mocked(refreshSession).mockResolvedValue(ROTATED)

    const store = useAuthStore()
    await store.refresh()

    expect(refreshSession).toHaveBeenCalledTimes(1)
    expect(store.accessToken).toBe('acc-2')
    expect(store.refreshToken).toBe('ref-2')
  })

  it('restoreIfNeeded restores a valid session from storage via /auth/me', async () => {
    storageState.accessToken = 'acc-1'
    storageState.refreshToken = 'ref-1'
    vi.mocked(authApi.me).mockResolvedValue(ANA)

    const store = useAuthStore()
    await store.restoreIfNeeded()

    expect(authApi.me).toHaveBeenCalledTimes(1)
    expect(store.user).toEqual(ANA)
    expect(store.role).toBe('admin')
    expect(store.isAuthenticated).toBe(true)
  })

  it('restoreIfNeeded rotates an expired token then re-fetches /auth/me', async () => {
    storageState.accessToken = 'acc-old'
    storageState.refreshToken = 'ref-old'
    vi.mocked(authApi.me).mockRejectedValueOnce(unauthorizedError())
    vi.mocked(authApi.me).mockResolvedValueOnce(ANA)
    vi.mocked(refreshSession).mockResolvedValue(ROTATED)

    const store = useAuthStore()
    await store.restoreIfNeeded()

    expect(refreshSession).toHaveBeenCalledTimes(1)
    expect(authApi.me).toHaveBeenCalledTimes(2)
    expect(store.accessToken).toBe('acc-2')
    expect(store.refreshToken).toBe('ref-2')
    expect(store.user).toEqual(ANA)
  })

  it('restoreIfNeeded clears the session when refresh also fails', async () => {
    storageState.accessToken = 'acc-old'
    storageState.refreshToken = 'ref-old'
    vi.mocked(authApi.me).mockRejectedValue(unauthorizedError())
    vi.mocked(refreshSession).mockRejectedValue(new Error('refresh token revoked'))

    const store = useAuthStore()
    await store.restoreIfNeeded()

    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(storageState.accessToken).toBeNull()
  })

  it('restoreIfNeeded keeps the session on a network error (no refresh, no clear)', async () => {
    storageState.accessToken = 'acc-1'
    storageState.user = ANA
    vi.mocked(authApi.me).mockRejectedValue(new Error('Network Error'))

    const store = useAuthStore()
    await store.restoreIfNeeded()

    expect(refreshSession).not.toHaveBeenCalled()
    expect(store.isAuthenticated).toBe(true)
    expect(store.user).toEqual(ANA)
  })

  it('restoreIfNeeded is a no-op when the store is already restored', async () => {
    const store = useAuthStore()
    store.$patch({ accessToken: 'acc-1', refreshToken: 'ref-1', user: ANA })

    await store.restoreIfNeeded()

    expect(authApi.me).not.toHaveBeenCalled()
  })

  it('logout invalidates the refresh token server-side and clears everything', async () => {
    vi.mocked(authApi.logout).mockResolvedValue(undefined)
    const store = useAuthStore()
    store.$patch({ accessToken: 'acc-1', refreshToken: 'ref-1', user: ANA })

    await store.logout()

    expect(authApi.logout).toHaveBeenCalledWith({ refresh_token: 'ref-1' })
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(storageState.accessToken).toBeNull()
    expect(storageState.refreshToken).toBeNull()
    expect(storageState.user).toBeNull()
  })

  it('getters reflect the current session state', () => {
    const store = useAuthStore()
    store.$patch({
      accessToken: 'acc-1',
      refreshToken: 'ref-1',
      user: { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol: 'operador' },
    })

    expect(store.isAuthenticated).toBe(true)
    expect(store.role).toBe('operador')
    expect(store.userName).toBe('Pepe Operador')

    store.$reset()
    expect(store.isAuthenticated).toBe(false)
    expect(store.role).toBeNull()
    expect(store.userName).toBe('')
  })
})
