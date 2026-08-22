import type { AxiosInstance } from 'axios'
import { readRefreshToken, writeTokens, clearTokens } from './storage'

let refreshClientInstance: AxiosInstance | null = null
let refreshPromise: Promise<string> | null = null

export function setRefreshClient(client: AxiosInstance): void {
  refreshClientInstance = client
}

export async function refreshSession(): Promise<string> {
  if (refreshPromise) {
    return refreshPromise
  }

  const refreshToken = readRefreshToken()
  if (!refreshToken) {
    clearTokens()
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
    }
    return Promise.reject(new Error('No refresh token available'))
  }

  refreshPromise = (async () => {
    try {
      if (refreshClientInstance) {
        const response = await refreshClientInstance.post('/auth/refresh', { refresh_token: refreshToken })
        const { access_token, refresh_token: newRefresh } = response.data
        writeTokens(access_token, newRefresh || refreshToken)
        return access_token
      }
      return 'mock-refreshed-token'
    } catch (err) {
      clearTokens()
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
      }
      throw err
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}
