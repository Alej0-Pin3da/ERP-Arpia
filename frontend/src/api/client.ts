/**
 * Typed API client (spec SHELL-2).
 *
 * - baseURL from VITE_API_BASE_URL (per-environment .env.* files)
 * - Bearer access token injected on every request from storage
 * - 401 -> single-flight refresh -> retry the original request ONCE
 * - unrecoverable 401 / refresh failure -> session cleared + /login
 */
import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios'

import { readAccessToken } from './storage'
import { refreshSession, setRefreshClient } from './refresh'
import { FORBIDDEN_MESSAGE } from './errors'
import { showToast } from '@/utils/toast'

export interface ClientOptions extends AxiosRequestConfig {
  /** Override the configured base URL (tests inject mocks via `adapter`). */
  baseURL?: string
}

/** Mark a request config as retried once (avoids infinite refresh loops). */
export interface RetryableRequestConfig extends AxiosRequestConfig {
  _retry?: boolean
}

export function createClient(options: ClientOptions = {}): AxiosInstance {
  const instance = axios.create({
    baseURL: options.baseURL ?? import.meta.env.VITE_API_BASE_URL,
    ...options,
  })

  // The refresh call itself uses this instance. Wired BEFORE any request can
  // 401 so the refresh flow never sees a stale lock.
  setRefreshClient(instance)

  attachInterceptors(instance)

  return instance
}

const IDEMPOTENT_PREFIXES = [
  '/ventas',
  '/devoluciones',
  '/compras',
  '/finanzas/movimientos',
  '/finanzas/liquidaciones',
  '/inventario/ajustes',
]

function requiresIdempotency(url?: string, method?: string): boolean {
  if (!url || !method) return false
  const m = method.toUpperCase()
  if (!['POST', 'PUT', 'PATCH'].includes(m)) return false
  return IDEMPOTENT_PREFIXES.some((p) => url.includes(p))
}

function hasIdempotencyHeader(headers: unknown): boolean {
  if (!headers) return false
  const h = headers as Record<string, unknown> & { get?: (k: string) => string | undefined }
  if (typeof h.get === 'function') return Boolean(h.get('Idempotency-Key'))
  return Boolean((h as Record<string, unknown>)['Idempotency-Key'])
}

function attachInterceptors(instance: AxiosInstance): void {
  instance.interceptors.request.use((config) => {
    const token = readAccessToken()
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`)
    }
    if (requiresIdempotency(config.url, config.method) && !hasIdempotencyHeader(config.headers)) {
      const uuid =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
      // AxiosHeaders has .set, plain object fallback uses bracket
      const headers = config.headers as unknown as { set?: (k: string, v: string) => void } & Record<string, string>
      if (typeof headers.set === 'function') headers.set('Idempotency-Key', uuid)
      else (config.headers as Record<string, string>)['Idempotency-Key'] = uuid
    }
    return config
  })

  instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<{ detail?: string }>) => {
      const config = error.config as RetryableRequestConfig | undefined
      const status = error.response?.status
      const isAuthEndpoint = config?.url?.includes('/auth/')

      // Runtime 403 (SHELL-5/BEH-2): the session's role cannot perform this
      // action. Surface a role-appropriate es-CO toast via the Toast
      // singleton, then keep the pass-through contract — the promise still
      // rejects so views can react (hide the offending action, etc.).
      if (status === 403) {
        showToast('error', 'Acceso denegado', FORBIDDEN_MESSAGE)
        return Promise.reject(error)
      }

      // Anything other than an expired-token 401 passes through untouched.
      if (status !== 401 || !config || config._retry || isAuthEndpoint) {
        return Promise.reject(error)
      }

      // Await the shared refresh; failure clears the session + redirects
      // (handled by refresh.ts) — surface it to the caller.
      try {
        await refreshSession()
      } catch (refreshError) {
        return Promise.reject(refreshError)
      }

      // Replay the failed request once with the NEW access token.
      config._retry = true
      return instance.request(config)
    },
  )
}

export type { AxiosInstance }

/** Singleton used across the app (endpoints.ts wrappers). */
export const client: AxiosInstance = createClient()
