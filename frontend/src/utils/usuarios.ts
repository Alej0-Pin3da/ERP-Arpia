/**
 * Usuarios mappers (PR11, spec MOD-5 usuarios part).
 *
 * Admin-only module (route meta.roles ['admin'] + require_admin on every
 * /usuarios endpoint). Pure helpers here:
 *  - `USUARIO_ROLES` feeds the rol select (admin | operador | consulta,
 *    backend VALID_ROLES in app/schemas/usuario.py)
 *  - `rolTagType` maps a rol to its Element Plus tag color in the table
 *  - `buildUsuarioPayload` builds the exact UsuarioCreate body (nombre,
 *    email, rol, password). The password is NOT trimmed — it is a secret and
 *    every character counts; the form enforces min 6 chars (schema
 *    min_length=6).
 *  - `buildUsuarioUpdatePayload` builds the rol-only UsuarioUpdate — the
 *    module's edit action changes only the rol. A self-demote (PATCH own
 *    rol away from admin) is rejected by the backend with 400
 *    "Cannot change your own role away from admin"; the view surfaces it.
 */
import type { components } from '@/types/api.d'

type UsuarioCreate = components['schemas']['UsuarioCreate']
type UsuarioUpdate = components['schemas']['UsuarioUpdate']

/** Valid roles in select order (backend VALID_ROLES). */
export const USUARIO_ROLES = ['admin', 'operador', 'consulta'] as const

export type UsuarioRol = (typeof USUARIO_ROLES)[number]

/** Element Plus tag type per rol for the list table. */
export function rolTagType(rol: string): 'danger' | 'primary' | 'info' {
  switch (rol) {
    case 'admin':
      return 'danger'
    case 'operador':
      return 'primary'
    default:
      return 'info'
  }
}

/** Exact UsuarioCreate body. Password stays exactly as typed (never trimmed). */
export function buildUsuarioPayload(values: {
  nombre: string
  email: string
  rol: string
  password: string
}): UsuarioCreate {
  return {
    nombre: values.nombre.trim(),
    email: values.email.trim(),
    rol: values.rol,
    password: values.password,
  }
}

/** Rol-only UsuarioUpdate — the edit form only changes the rol. */
export function buildUsuarioUpdatePayload(rol: string): UsuarioUpdate {
  return { rol }
}
