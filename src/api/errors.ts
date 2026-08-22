import { AxiosError } from 'axios'

export const FORBIDDEN_MESSAGE = 'No tiene permisos suficientes para realizar esta acción en el Atelier.'

export function isUnauthorized(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 401
  }
  if (error && typeof error === 'object' && 'status' in error) {
    return (error as { status: number }).status === 401
  }
  return false
}

export function isForbidden(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 403
  }
  if (error && typeof error === 'object' && 'status' in error) {
    return (error as { status: number }).status === 403
  }
  return false
}
