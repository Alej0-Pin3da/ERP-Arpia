/**
 * Token persistence (localStorage).
 *
 * Design decision: tokens live in localStorage (backend returns them in the
 * JSON body, no cookie support; rotation REQUIRES persistence). The XSS
 * tradeoff is documented in the design — accepted for this SPA.
 */
import type { UsuarioRead } from './types'

export const STORAGE_KEYS = {
  access: 'arpia_access',
  refresh: 'arpia_refresh',
  user: 'arpia_user',
} as const

/** Read the current access token, or null when absent. */
export function readAccessToken(): string | null {
  return read(STORAGE_KEYS.access)
}

/** Read the current refresh token, or null when absent. */
export function readRefreshToken(): string | null {
  return read(STORAGE_KEYS.refresh)
}

/**
 * Persist the rotated token pair. ORDER MATTERS (design learning #4):
 * `refresh` and `access` are written BEFORE any queued 401 retry resolves,
 * so a retry can never fire with a stale refresh token (backend reuse
 * detection revokes ALL sessions).
 */
export function writeTokens(access: string, refresh: string): void {
  try {
    window.localStorage.setItem(STORAGE_KEYS.access, access)
    window.localStorage.setItem(STORAGE_KEYS.refresh, refresh)
  } catch {
    // Storage unavailable (privacy mode / quota) — session is volatile.
  }
}

/** Persist the authoritative user payload (id/nombre/email/rol). */
export function writeUser(user: unknown): void {
  try {
    window.localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user))
  } catch {
    // Non-fatal.
  }
}

/**
 * Read the cached user payload. Returns null when absent or malformed —
 * the auth store treats /auth/me as authoritative and overwrites this cache.
 */
export function readUser(): UsuarioRead | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEYS.user)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<UsuarioRead> | null
    if (
      parsed &&
      typeof parsed.id === 'number' &&
      typeof parsed.nombre === 'string' &&
      typeof parsed.email === 'string' &&
      typeof parsed.rol === 'string'
    ) {
      return parsed as UsuarioRead
    }
    return null
  } catch {
    return null
  }
}

/** Clear every session key (used on refresh failure and logout). */
export function clearSession(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEYS.access)
    window.localStorage.removeItem(STORAGE_KEYS.refresh)
    window.localStorage.removeItem(STORAGE_KEYS.user)
  } catch {
    // Non-fatal.
  }
}

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}
