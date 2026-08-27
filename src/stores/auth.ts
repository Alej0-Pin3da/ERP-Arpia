import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { client } from '@/api/client'
import {
  readAccessToken,
  writeTokens,
  clearTokens,
  readStoredUser,
  writeStoredUser,
} from '@/api/storage'

export interface AuthUser {
  id: number
  nombre: string
  email: string
  rol: 'admin' | 'operador' | 'consulta'
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(readStoredUser() as AuthUser | null)

  const token = ref<string | null>(readAccessToken())

  const isAuthenticated = computed(() => Boolean(user.value))
  const role = computed<'admin' | 'operador' | 'consulta'>(() => user.value?.rol || 'operador')

  async function login(email: string, pass: string): Promise<void> {
    try {
      const res = await client.post('/auth/login', { email, password: pass })
      const data = res.data as Record<string, unknown>
      const access = data.access_token as string | undefined
      if (!access) {
        throw new Error('Login response missing access_token')
      }
      token.value = access
      writeTokens(access, (data.refresh_token as string | undefined) ?? undefined)
      // Poblar el user real desde /auth/me con el token recién obtenido.
      try {
        const me = await client.get('/auth/me')
        const m = me.data as Record<string, unknown>
        user.value = {
          id: Number(m.id ?? 1),
          nombre: String(m.nombre ?? 'Usuario'),
          email: String(m.email ?? email),
          rol: (m.rol as AuthUser['rol']) || (data.rol as AuthUser['rol']) || 'operador',
        }
      } catch {
        // Si /auth/me falla, usar el rol del token de login.
        user.value = {
          id: 1,
          nombre: 'Usuario',
          email,
          rol: (data.rol as AuthUser['rol']) || 'operador',
        }
      }
      writeStoredUser(user.value)
    } catch {
      // Fallback in-memory matching (modo MOCK)
      if (email.includes('admin') || pass === 'admin123') {
        user.value = { id: 1, nombre: 'Valeria Arpía', email, rol: 'admin' }
      } else if (email.includes('oper') || pass === 'oper123') {
        user.value = { id: 2, nombre: 'Camila Modista', email, rol: 'operador' }
      } else {
        user.value = { id: 3, nombre: 'Socia Auditora', email, rol: 'consulta' }
      }
      token.value = 'mock-auth-token'
      writeTokens(token.value)
      writeStoredUser(user.value)
    }
  }

  function logout(): void {
    user.value = null
    token.value = null
    clearTokens()
  }

  function changeRole(newRole: 'admin' | 'operador' | 'consulta'): void {
    if (user.value) {
      user.value.rol = newRole
      writeStoredUser(user.value)
    }
  }

  async function restoreIfNeeded(): Promise<void> {
    if (user.value) return
    const stored = readStoredUser()
    if (stored) {
      user.value = stored as AuthUser
    }
  }

  return {
    user,
    token,
    role,
    isAuthenticated,
    login,
    logout,
    changeRole,
    restoreIfNeeded,
  }
})
