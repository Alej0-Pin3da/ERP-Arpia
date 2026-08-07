/**
 * Runtime 403 surfacing tests (task 1.7, spec SHELL-5).
 *
 * A 403 means the session's role cannot perform the invoked action. The
 * API client's response interceptor surfaces an Element Plus es-CO message
 * while STILL rejecting the promise — the pass-through design from PR2 is
 * preserved, so views can also react programmatically (hide/disable the
 * offending action).
 *
 * The backend sends an English detail ("Role 'operador' is not allowed to
 * perform this action") — the frontend message is fixed Spanish per the
 * es-CO UI convention.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

import { FORBIDDEN_MESSAGE } from '@/api/errors'

// --- module mocks -----------------------------------------------------------

const messageSpy = vi.fn()
vi.mock('element-plus', () => ({
  ElMessage: { error: (msg: string) => messageSpy(msg) },
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

describe('runtime 403 surfacing (spec SHELL-5)', () => {
  beforeEach(() => {
    messageSpy.mockClear()
  })

  it('shows the role-restriction message on a 403 and still rejects the call', async () => {
    const client = await freshClient(() => ({ status: 403, data: {} }))

    await expect(client.get('/ventas')).rejects.toThrow()

    expect(messageSpy).toHaveBeenCalledTimes(1)
    expect(messageSpy).toHaveBeenCalledWith(FORBIDDEN_MESSAGE)
  })

  it('uses the es-CO message, never the English server detail', async () => {
    const client = await freshClient(() => ({
      status: 403,
      data: { detail: "Role 'operador' is not allowed to perform this action" },
    }))

    await expect(client.get('/usuarios')).rejects.toThrow()

    expect(messageSpy).toHaveBeenCalledWith(FORBIDDEN_MESSAGE)
    expect(messageSpy).toHaveBeenCalledTimes(1)
  })

  it('passes non-403 errors through without a message (PR2 pass-through preserved)', async () => {
    const client = await freshClient(() => ({ status: 422, data: { detail: 'Invalid payload' } }))

    await expect(client.post('/ventas', {})).rejects.toThrow()

    expect(messageSpy).not.toHaveBeenCalled()
  })
})
