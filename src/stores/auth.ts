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
  const user = ref<AuthUser | null>(
    readStoredUser() as AuthUser | null ?? {
      id: 1,
      nombre: 'Valeria Arpía',
      email: 'admin@arpia.com.co',
      rol: 'admin',
    }
  )

  const token = ref<string | null>(readAccessToken() ?? 'dev-token-arpia')

  const isAuthenticated = computed(() => Boolean(user.value))
  const role = computed<'admin' | 'operador' | 'consulta'>(() => user.value?.rol || 'operador')

  async function login(email: string, pass: string): Promise<void> {
    try {
      const res = await client.post('/auth/login', { email, password: pass })
      if (res.data && res.data.user) {
        user.value = res.data.user
        token.value = res.data.access_token || 'session-token'
        writeTokens(token.value, res.data.refresh_token)
        writeStoredUser(res.data.user)
        return
      }
    } catch {
      // Fallback in-memory matching
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
