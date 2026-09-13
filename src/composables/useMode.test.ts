import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { useMode } from './useMode'

describe('useMode', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('is always REAL even when VITE_USE_MOCK=true (mock removed)', () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const { mode, isMock } = useMode()
    expect(mode.value).toBe('REAL')
    expect(isMock.value).toBe(false)
  })

  it('is REAL when VITE_USE_MOCK is false', () => {
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

  it('refresh resolves REAL and marks liveChecked without fetching', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    const { mode, isMock, liveChecked, refresh } = useMode()
    await refresh()
    expect(mode.value).toBe('REAL')
    expect(isMock.value).toBe(false)
    expect(liveChecked.value).toBe(true)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('badge contract: mode is REAL only', () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const { mode } = useMode()
    expect(mode.value).toBe('REAL')
  })

  it('envMode always resolves REAL', () => {
    const { envMode } = useMode()
    expect(envMode()).toBe('REAL')
  })
})
