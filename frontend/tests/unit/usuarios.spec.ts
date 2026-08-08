/**
 * Usuarios mapper tests (PR11, spec MOD-5 usuarios part).
 *
 * Pure functions only, zero mocks:
 *  - `USUARIO_ROLES` + `rolTagType` drive the rol select + table tag
 *  - `buildUsuarioPayload` builds the exact UsuarioCreate (nombre, email,
 *    rol, password — password never empty, all fields trimmed)
 *  - `buildUsuarioUpdatePayload` builds the rol-only UsuarioUpdate — editing
 *    a user only changes their rol per the module scope; a self-demote is
 *    rejected server-side (400) and surfaced by the view.
 */
import { describe, expect, it } from 'vitest'

import {
  buildUsuarioPayload,
  buildUsuarioUpdatePayload,
  rolTagType,
  USUARIO_ROLES,
} from '@/utils/usuarios'

describe('USUARIO_ROLES (MOD-5 usuarios)', () => {
  it('exposes the three valid roles in select order', () => {
    expect(USUARIO_ROLES).toEqual(['admin', 'operador', 'consulta'])
  })

  it('maps roles to Element Plus tag types for the table', () => {
    expect(rolTagType('admin')).toBe('danger')
    expect(rolTagType('operador')).toBe('primary')
    expect(rolTagType('consulta')).toBe('info')
  })

  it('falls back to info for unknown roles', () => {
    expect(rolTagType('superuser')).toBe('info')
  })
})

describe('buildUsuarioPayload', () => {
  it('builds the exact UsuarioCreate body, trimming every field', () => {
    expect(
      buildUsuarioPayload({
        nombre: '  María Pérez ',
        email: 'maria@arpia.com.co',
        rol: 'operador',
        password: 'clave123',
      }),
    ).toEqual({
      nombre: 'María Pérez',
      email: 'maria@arpia.com.co',
      rol: 'operador',
      password: 'clave123',
    })
  })

  it('keeps the password exactly as typed (never trimmed) and supports the consulta default rol', () => {
    expect(
      buildUsuarioPayload({
        nombre: 'Luis',
        email: 'luis@arpia.com.co',
        rol: 'consulta',
        password: ' s3cret ',
      }),
    ).toEqual({
      nombre: 'Luis',
      email: 'luis@arpia.com.co',
      rol: 'consulta',
      password: ' s3cret ',
    })
  })
})

describe('buildUsuarioUpdatePayload', () => {
  it('builds the rol-only UsuarioUpdate used by the edit form', () => {
    expect(buildUsuarioUpdatePayload('consulta')).toEqual({ rol: 'consulta' })
  })
})
