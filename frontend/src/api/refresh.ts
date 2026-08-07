/**
 * Single-flight refresh — the critical race guard (design "Refresh Race
 * Algorithm" + learning #4).
 *
 * Module state holds ONE shared promise. Every 401 arriving while a refresh is
 * in flight awaits the SAME promise — a second refresh call can never be fired
 * with the same refresh token (backend reuse detection revokes ALL sessions).
 *
 * Order of operations on success (DO NOT reorder):
 *   1. POST /auth/refresh with the CURRENT refresh token
 *   2. persist the NEW access + refresh tokens to storage
 *   3. ONLY THEN resolve the shared promise
 * A queued 401 retry resumes after (3), reads the NEW access token and replays
 * the original request once. If it 401s again, the session is unrecoverable.
 */
import type { AxiosInstance } from 'axios'

import { clearSession, readRefreshToken, writeTokens } from './storage'
import { redirectToLogin } from './redirect'

/** Minimal token envelope returned by POST /auth/refresh. */
export interface RefreshTokenPayload {
  access_token: string
  refresh_token: string
  rol?: string
}

let refreshPromise: Promise<RefreshTokenPayload> | null = null

/** Wire the axios instance used for the refresh call itself (set once by
 * the client module at creation time — avoids a client<->refresh cycle). */
export function setRefreshClient(instance: AxiosInstance): void {
  refreshClient = instance
}

let refreshClient: AxiosInstance | null = null

/**
 * Resolve a shared refresh. Returns the NEW token payload.
 * - success: tokens persisted BEFORE the promise resolves (order matters)
 * - failure: session cleared + single redirect to /login, promise rejects
 */
export function refreshSession(): Promise<RefreshTokenPayload> {
  if (refreshPromise) {
    return refreshPromise
  }

  const current = readRefreshToken()
  if (!current) {
    // Nothing to rotate with — unrecoverable. Design step 4.
    clearSession()
    redirectToLogin('/login')
    return Promise.reject(new Error('No refresh token available'))
  }

  refreshPromise = doRefresh(current)
  // Keep the module lock from poisoning future attempts after settle.
  refreshPromise
    .catch(() => undefined)
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

async function doRefresh(refreshToken: string): Promise<RefreshTokenPayload> {
  if (!refreshClient) {
    throw new Error('Refresh client not wired')
  }
  try {
    const { data } = await refreshClient.post<RefreshTokenPayload>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    // Persist BEFORE resolving — queued retries must never see a stale token.
    writeTokens(data.access_token, data.refresh_token)
    return data
  } catch (err) {
    clearSession()
    redirectToLogin('/login')
    throw err
  }
}
