const ACCESS_TOKEN_KEY = 'arpia_access_token'
const REFRESH_TOKEN_KEY = 'arpia_refresh_token'
const USER_KEY = 'arpia_user_data'

export function readAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  } catch {
    return null
  }
}

export function readRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  } catch {
    return null
  }
}

export function writeTokens(access: string, refresh?: string): void {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    if (refresh) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    }
  } catch {
    // Ignore storage errors
  }
}

export function clearTokens(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  } catch {
    // Ignore storage errors
  }
}

export function readStoredUser(): { id: number; nombre: string; email: string; rol: string } | null {
  try {
    const data = localStorage.getItem(USER_KEY)
    return data ? JSON.parse(data) : null
  } catch {
    return null
  }
}

export function writeStoredUser(user: { id: number; nombre: string; email: string; rol: string }): void {
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  } catch {
    // Ignore storage errors
  }
}
