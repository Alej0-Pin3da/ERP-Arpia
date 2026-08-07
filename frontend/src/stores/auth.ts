/**
 * Pinia auth store (task 1.5, spec SHELL-3).
 *
 * Owns the client-side session: tokens + the authoritative user (id, nombre,
 * email, rol). Storage persistence lives in `api/storage.ts`
 * (arpia_access / arpia_refresh / arpia_user); the single-flight refresh in
 * `api/refresh.ts` owns the 401 rotation on the HTTP layer. This store:
 *
 * - `login(email, password)`: POST /auth/login -> persist tokens -> GET
 *   /auth/me (authoritative user) -> persist user.
 * - `refresh()`: rotate via the shared single-flight refresh and sync state.
 * - `logout()`: POST /auth/logout with the refresh token (204 expected),
 *   then clear storage + state unconditionally.
 * - `restoreIfNeeded()`: on reload, reconcile from storage — /auth/me first;
 *   a 401 rotates through the refresh flow and re-fetches; refresh failure
 *   clears the session. Network errors never clear (design step 5).
 *
 * The router guard awaits `restoreIfNeeded()` BEFORE evaluating `meta.roles`
 * (design learning #5 — avoids the role-guard race on reload).
 */
import { defineStore } from 'pinia'

import { authApi } from '@/api/endpoints'
import { isUnauthorized } from '@/api/errors'
import { refreshSession } from '@/api/refresh'
import {
  clearSession,
  readAccessToken,
  readRefreshToken,
  readUser,
  writeTokens,
  writeUser,
} from '@/api/storage'
import type { UsuarioRead } from '@/api/types'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  /** Authoritative user from /auth/me (UsuarioRead = id, nombre, email, rol). */
  user: UsuarioRead | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: null,
    refreshToken: null,
    user: null,
  }),

  getters: {
    isAuthenticated: (state): boolean => Boolean(state.accessToken),
    role: (state): string | null => state.user?.rol ?? null,
    userName: (state): string => state.user?.nombre ?? '',
  },

  actions: {
    /** Login: persist tokens + authoritative user. Rethrows so the view can
     * surface a 401 as "incorrect credentials". */
    async login(email: string, password: string): Promise<void> {
      const data = await authApi.login({ email, password })
      writeTokens(data.access_token, data.refresh_token)
      this.accessToken = data.access_token
      this.refreshToken = data.refresh_token

      // The token envelope only carries `rol` — fetch the full user for the
      // header/guards. Best-effort: the guard reconciles via restoreIfNeeded
      // on the next navigation if this fails.
      try {
        const me = await authApi.me()
        this.user = me
        writeUser(me)
      } catch {
        // Tokens are already valid and persisted; user resolves on navigation.
      }
    },

    /** Rotate tokens through the shared single-flight refresh (storage is
     * persisted by refresh.ts). */
    async refresh(): Promise<void> {
      try {
        const data = await refreshSession()
        this.accessToken = data.access_token
        this.refreshToken = data.refresh_token
      } catch (err) {
        this.$reset()
        throw err
      }
    },

    /** Logout: invalidate the refresh token server-side, then clear storage
     * + state even if the network call fails (local logout must always win). */
    async logout(): Promise<void> {
      const refresh = this.refreshToken ?? readRefreshToken()
      try {
        if (refresh) {
          await authApi.logout({ refresh_token: refresh })
        }
      } finally {
        clearSession()
        this.$reset()
      }
    },

    /** On reload: reconcile the session from storage. No-op when the store
     * already holds a restored session (login flow / repeated guard runs). */
    async restoreIfNeeded(): Promise<void> {
      if (this.accessToken && this.user) {
        return
      }

      const access = readAccessToken()
      if (!access) {
        this.$reset()
        return
      }

      // Fast-path: cached user renders the header immediately; /auth/me below
      // is authoritative and overwrites it.
      this.accessToken = access
      this.refreshToken = readRefreshToken()
      this.user = readUser()

      try {
        const me = await authApi.me()
        this.user = me
        writeUser(me)
      } catch (err) {
        if (isUnauthorized(err)) {
          // Expired access token: rotate through the single-flight refresh,
          // then re-fetch the authoritative user.
          try {
            const data = await refreshSession()
            this.accessToken = data.access_token
            this.refreshToken = data.refresh_token
            const me = await authApi.me()
            this.user = me
            writeUser(me)
          } catch {
            // Refresh failed — refresh.ts already cleared storage + redirected.
            clearSession()
            this.$reset()
          }
        }
        // Network error (no response): keep the session + cached user
        // (design step 5 — never clear on connectivity problems).
      }
    },
  },
})
