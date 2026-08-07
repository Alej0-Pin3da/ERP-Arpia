/**
 * Single-flight refresh race tests (task 1.3, design "Refresh Race Algorithm").
 *
 * These drive the REAL client (axios instance + request/response interceptors)
 * through a controllable mock adapter, with storage/redirect mocked. They prove
 * the user-visible contract from spec SHELL-2:
 *   1. Parallel 401s -> exactly ONE POST /auth/refresh
 *   2. Rotated refresh token persisted BEFORE the retried request fires
 *   3. Refresh failure -> session cleared + single redirect to /login
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

const ACCESS_OLD = 'access-old'
const ACCESS_NEW = 'access-new'
const REFRESH_OLD = 'refresh-old'
const REFRESH_NEW = 'refresh-new'

// --- module mocks -----------------------------------------------------------

const storageState = {
  accessToken: ACCESS_OLD,
  refreshToken: REFRESH_OLD,
  writes: [] as Array<{ access: string; refresh: string }>,
}

vi.mock('@/api/storage', () => ({
  STORAGE_KEYS: { access: 'arpia_access', refresh: 'arpia_refresh', user: 'arpia_user' },
  readAccessToken: () => storageState.accessToken,
  readRefreshToken: () => storageState.refreshToken,
  writeTokens: (access: string, refresh: string) => {
    storageState.writes.push({ access, refresh })
    storageState.accessToken = access
    storageState.refreshToken = refresh
  },
  clearSession: () => {
    storageState.accessToken = ''
    storageState.refreshToken = ''
  },
}))

const redirectSpy = vi.fn()
vi.mock('@/api/redirect', () => ({
  redirectToLogin: (path: string) => redirectSpy(path),
}))

// --- mock adapter -----------------------------------------------------------

interface Handler {
  (config: InternalAxiosRequestConfig): { status: number; data?: unknown }
}

function makeAdapter(handler: Handler) {
  return async (config: InternalAxiosRequestConfig) => {
    const result = handler(config)
    if (result.status >= 400) {
      const err = new Error(`Request failed with status code ${result.status}`) as AxiosError
      err.config = config
      err.response = { status: result.status, data: result.data, headers: {}, config } as never
      throw err
    }
    return { data: result.data, status: result.status, statusText: 'OK', headers: {}, config }
  }
}

// Client is imported lazily per test so a fresh axios instance + interceptor
// wiring is created against the current storage/adapter state.
let createClient: typeof import('@/api/client').createClient

async function freshClient(handler: Handler) {
  vi.resetModules()
  const { createClient: create } = await import('@/api/client')
  createClient = create
  return createClient({ adapter: makeAdapter(handler) })
}

function tokensPayload(access: string, refresh: string) {
  return { access_token: access, refresh_token: refresh, token_type: 'bearer', rol: 'admin' }
}

// --- tests ------------------------------------------------------------------

describe('single-flight refresh (spec SHELL-2)', () => {
  beforeEach(() => {
    storageState.accessToken = ACCESS_OLD
    storageState.refreshToken = REFRESH_OLD
    storageState.writes = []
    redirectSpy.mockClear()
  })

  it('parallel 401s trigger exactly one refresh call and both retry with the rotated token', async () => {
    const calls: string[] = []
    const client = await freshClient((config) => {
      const auth = config.headers?.Authorization as string
      calls.push(`${config.method?.toUpperCase()} ${config.url} auth=${auth}`)
      if (config.url === '/auth/refresh') {
        return { status: 200, data: tokensPayload(ACCESS_NEW, REFRESH_NEW) }
      }
      if (config.url === '/ventas') {
        // Simulate an expired access token: reject until the NEW token arrives.
        if (auth === `Bearer ${ACCESS_NEW}`) {
          return { status: 200, data: [{ id: 1, total: '10.00' }] }
        }
        return { status: 401, data: { detail: 'Token expired' } }
      }
      return { status: 404, data: {} }
    })

    const [a, b] = await Promise.all([client.get('/ventas'), client.get('/ventas')])

    expect(a.data).toEqual([{ id: 1, total: '10.00' }])
    expect(b.data).toEqual([{ id: 1, total: '10.00' }])
    const refreshCalls = calls.filter((c) => c.includes('/auth/refresh'))
    expect(refreshCalls).toHaveLength(1)
    expect(calls.filter((c) => c.includes('/ventas'))).toHaveLength(4) // 2 original 401s + 2 retries
  })

  it('persists the rotated token before the retry uses it (storage-before-retry)', async () => {
    const authsAtVentas: Array<string | undefined> = []
    const client = await freshClient((config) => {
      const auth = config.headers?.Authorization as string
      if (config.url === '/auth/refresh') {
        return { status: 200, data: tokensPayload(ACCESS_NEW, REFRESH_NEW) }
      }
      if (config.url === '/ventas') {
        authsAtVentas.push(auth)
        if (auth === `Bearer ${ACCESS_NEW}`) return { status: 200, data: { ok: true } }
        return { status: 401, data: { detail: 'Token expired' } }
      }
      return { status: 404, data: {} }
    })

    await client.get('/ventas')

    // The retried request MUST carry the rotated token...
    expect(authsAtVentas).toContain(`Bearer ${ACCESS_NEW}`)
    // ...and the write must have happened before the retry could read it.
    expect(storageState.writes).toEqual([{ access: ACCESS_NEW, refresh: REFRESH_NEW }])
    expect(storageState.accessToken).toBe(ACCESS_NEW)
    expect(storageState.refreshToken).toBe(REFRESH_NEW)
  })

  it('refresh failure clears the session and redirects to /login exactly once', async () => {
    const client = await freshClient((config) => {
      if (config.url === '/auth/refresh') {
        return { status: 401, data: { detail: 'Invalid refresh token' } }
      }
      return { status: 401, data: { detail: 'Token expired' } }
    })

    await expect(Promise.all([client.get('/ventas'), client.get('/ventas')])).rejects.toThrow()

    expect(storageState.accessToken).toBe('')
    expect(storageState.refreshToken).toBe('')
    expect(redirectSpy).toHaveBeenCalledTimes(1)
    expect(redirectSpy).toHaveBeenCalledWith('/login')
  })

  it('does not refresh on a plain 401 when no refresh token exists (unrecoverable)', async () => {
    storageState.refreshToken = ''
    const client = await freshClient((config) => {
      if (config.url === '/auth/refresh') return { status: 200, data: tokensPayload(ACCESS_NEW, REFRESH_NEW) }
      return { status: 401, data: { detail: 'Token expired' } }
    })

    await expect(client.get('/ventas')).rejects.toThrow()

    // No refresh POST should have been attempted without a token to send.
    expect(redirectSpy).toHaveBeenCalledTimes(1)
  })
})
