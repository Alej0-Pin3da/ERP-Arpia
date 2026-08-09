/**
 * Role-aware menu tests (task 1.7, spec SHELL-4/SHELL-5).
 *
 * `RoleMenuFilter` is the pure function behind the sidebar: it takes the
 * current role and returns only the menu items that role may access
 * (Usuarios is admin-only). `roleLabel` renders the human es-CO role name
 * for the header badge.
 */
import { describe, expect, it } from 'vitest'

import { MENU_ITEMS, RoleMenuFilter, roleLabel, type MenuItem } from '@/utils/menu'

describe('RoleMenuFilter (spec SHELL-4)', () => {
  it('exposes the full menu with the admin-only Usuarios item flagged', () => {
    // 9 sections: Dashboard, Ventas, Devoluciones, Finanzas, Inventario,
    // Productos, Maestros, Omisiones, Usuarios.
    expect(MENU_ITEMS).toHaveLength(9)
    const labels = MENU_ITEMS.map((item) => item.label)
    expect(labels).toEqual([
      'Dashboard',
      'Ventas',
      'Devoluciones',
      'Finanzas',
      'Inventario',
      'Productos',
      'Maestros',
      'Omisiones',
      'Usuarios',
    ])
    expect(MENU_ITEMS.find((item) => item.label === 'Usuarios')?.roles).toEqual(['admin'])
    expect(MENU_ITEMS.find((item) => item.label === 'Omisiones')?.roles).toEqual([
      'admin',
      'operador',
      'consulta',
    ])
  })

  it('gives an admin every menu item, including Usuarios', () => {
    const items = RoleMenuFilter('admin')

    expect(items).toHaveLength(9)
    expect(items.map((item) => item.label)).toContain('Usuarios')
    expect(items.map((item) => item.label)).toContain('Omisiones')
  })

  it('hides the admin-only Usuarios item from an operador', () => {
    const items = RoleMenuFilter('operador')

    expect(items).toHaveLength(8)
    const labels = items.map((item) => item.label)
    expect(labels).not.toContain('Usuarios')
    expect(labels).toContain('Ventas')
    expect(labels).toContain('Dashboard')
    expect(labels).toContain('Omisiones')
  })

  it('hides the admin-only Usuarios item from a consulta', () => {
    const items = RoleMenuFilter('consulta')

    expect(items).toHaveLength(8)
    expect(items.map((item) => item.label)).not.toContain('Usuarios')
    expect(items.map((item) => item.label)).toContain('Omisiones')
  })

  it('returns an empty menu for an unknown or missing role', () => {
    expect(RoleMenuFilter(null)).toEqual([])
    expect(RoleMenuFilter('auditor')).toEqual([])
  })

  it('filters a custom item set by role (order preserved)', () => {
    const custom: MenuItem[] = [
      { name: 'a', path: '/a', label: 'A', roles: ['admin'] },
      { name: 'b', path: '/b', label: 'B', roles: ['operador'] },
      { name: 'c', path: '/c', label: 'C', roles: ['admin', 'operador'] },
    ]
    const items = RoleMenuFilter('operador', custom)

    expect(items).toHaveLength(2)
    expect(items.map((item) => item.label)).toEqual(['B', 'C'])
  })
})

describe('roleLabel (spec SHELL-5 header badge)', () => {
  it('maps each role to its es-CO label', () => {
    expect(roleLabel('admin')).toBe('Administrador')
    expect(roleLabel('operador')).toBe('Operador')
    expect(roleLabel('consulta')).toBe('Consulta')
  })

  it('returns an empty string for a missing role', () => {
    expect(roleLabel(null)).toBe('')
    expect(roleLabel('')).toBe('')
  })
})
