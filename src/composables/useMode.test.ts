import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

import { useMode } from './useMode'

describe('useMode', () => {
  let origFetch: typeof globalThis.fetch

  beforeEach(() => {
    setActivePinia(createPinia())
    origFetch = globalThis.fetch
    vi.restoreAllMocks()
  })

  afterEach(() => {
    globalThis.fetch = origFetch
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('defaults to MOCK when VITE_USE_MOCK is true', () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const { mode, isMock } = useMode()
    expect(mode.value).toBe('MOCK')
    expect(isMock.value).toBe(true)
  })

  it('returns REAL when VITE_USE_MOCK is false', () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const { mode, isMock } = useMode()
    expect(mode.value).toBe('REAL')
    expect(isMock.value).toBe(false)
  })

  it('treats external VITE_API_BASE_URL as REAL when USE_MOCK not set', () => {
    vi.stubEnv('VITE_USE_MOCK', '')
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000/api/v1')
    const { mode } = useMode()
    expect(mode.value).toBe('REAL')
  })

  it('live probe GET /api/__mode real overrides env', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ mode: 'real' }),
    } as Response)
    const { mode, isMock, refresh } = useMode()
    // before probe still MOCK via env
    expect(mode.value).toBe('MOCK')
    await refresh()
    expect(mode.value).toBe('REAL')
    expect(isMock.value).toBe(false)
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/__mode', expect.any(Object))
  })

  it('live probe mock keeps MOCK', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ mode: 'mock' }),
    } as Response)
    const { mode, refresh } = useMode()
    await refresh()
    expect(mode.value).toBe('MOCK')
  })

  it('fetch failure keeps env fallback and marks liveChecked', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('network'))
    const { mode, liveChecked, refresh } = useMode()
    await refresh()
    expect(mode.value).toBe('MOCK')
    expect(liveChecked.value).toBe(true)
  })

  it('badge contract: mode is MOCK or REAL only', () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const { mode } = useMode()
    expect(['MOCK', 'REAL']).toContain(mode.value)
  })
})
