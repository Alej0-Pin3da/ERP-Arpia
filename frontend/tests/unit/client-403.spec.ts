/**
 * Runtime 403 surfacing tests (task S4-T3, spec BEH-2).
 *
 * A 403 means the session's role cannot perform the invoked action. The
 * API client's response interceptor surfaces an es-CO error toast through
 * the toast.ts module singleton (PrimeVue Toast host, D4) while STILL
 * rejecting the promise — the pass-through design is preserved, so views can
 * also react programmatically (hide/disable the offending action).
 *
 * The backend sends an English detail ("Role 'operador' is not allowed to
 * perform this action") — the frontend message is fixed Spanish per the
 * es-CO UI convention, surfaced as summary 'Acceso denegado'.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

import { FORBIDDEN_MESSAGE } from '@/api/errors'

// --- module mocks -----------------------------------------------------------

const toastSpy = vi.hoisted(() => vi.fn())
vi.mock('@/utils/toast', () => ({
  showToast: toastSpy,
  setToastInstance: vi.fn(),
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

async function freshClient(handler: Handler) {
  vi.resetModules()
  const { createClient } = await import('@/api/client')
  return createClient({ adapter: makeAdapter(handler) })
}

// --- tests ------------------------------------------------------------------

describe('runtime 403 surfacing (spec BEH-2)', () => {
  beforeEach(() => {
    toastSpy.mockClear()
  })

  it('shows the role-restriction toast on a 403 and still rejects the call', async () => {
    const client = await freshClient(() => ({ status: 403, data: {} }))

    await expect(client.get('/ventas')).rejects.toThrow()

    expect(toastSpy).toHaveBeenCalledTimes(1)
    expect(toastSpy).toHaveBeenCalledWith('error', 'Acceso denegado', FORBIDDEN_MESSAGE)
  })

  it('uses the es-CO message, never the English server detail', async () => {
    const client = await freshClient(() => ({
      status: 403,
      data: { detail: "Role 'operador' is not allowed to perform this action" },
    }))

    await expect(client.get('/usuarios')).rejects.toThrow()

    expect(toastSpy).toHaveBeenCalledWith('error', 'Acceso denegado', FORBIDDEN_MESSAGE)
    expect(toastSpy).toHaveBeenCalledTimes(1)
  })

  it('passes non-403 errors through without a toast (pass-through preserved)', async () => {
    const client = await freshClient(() => ({ status: 422, data: { detail: 'Invalid payload' } }))

    await expect(client.post('/ventas', {})).rejects.toThrow()

    expect(toastSpy).not.toHaveBeenCalled()
  })
})
