/**
 * Role-aware sidebar configuration (task 1.7, spec SHELL-4/SHELL-5).
 *
 * `MENU_ITEMS` is the single source of truth for the sidebar navigation:
 * each item carries the roles that may see it (Usuarios is admin-only).
 * `RoleMenuFilter(role)` returns the subset the current role may access —
 * the pure function the SidebarMenu component renders, so the menu can
 * never drift from what the role guard (meta.roles) allows.
 */

export type MenuRole = 'admin' | 'operador' | 'consulta'

export interface MenuItem {
  /** Route name (matches a router record's `name`). */
  name: string
  /** Route path — drives ElMenu router mode + active highlighting. */
  path: string
  /** es-CO sidebar label. */
  label: string
  /** Roles allowed to see this item. */
  roles: MenuRole[]
}

export const MENU_ITEMS: MenuItem[] = [
  { name: 'dashboard', path: '/dashboard', label: 'Dashboard', roles: ['admin', 'operador', 'consulta'] },
  { name: 'ventas', path: '/ventas', label: 'Ventas', roles: ['admin', 'operador', 'consulta'] },
  { name: 'devoluciones', path: '/devoluciones', label: 'Devoluciones', roles: ['admin', 'operador', 'consulta'] },
  { name: 'finanzas', path: '/finanzas', label: 'Finanzas', roles: ['admin', 'operador', 'consulta'] },
  { name: 'inventario', path: '/inventario', label: 'Inventario', roles: ['admin', 'operador', 'consulta'] },
  { name: 'productos', path: '/productos', label: 'Productos', roles: ['admin', 'operador', 'consulta'] },
  { name: 'maestros', path: '/maestros', label: 'Maestros', roles: ['admin', 'operador', 'consulta'] },
  { name: 'omisiones', path: '/omisiones', label: 'Omisiones', roles: ['admin', 'operador', 'consulta'] },
  { name: 'usuarios', path: '/usuarios', label: 'Usuarios', roles: ['admin'] },
]

/** Human es-CO role names for the header badge. */
const ROLE_LABELS: Record<MenuRole, string> = {
  admin: 'Administrador',
  operador: 'Operador',
  consulta: 'Consulta',
}

/** es-CO label for a role (header badge); empty when no role is set. */
export function roleLabel(role: string | null): string {
  if (!role) return ''
  return ROLE_LABELS[role as MenuRole] ?? role
}

/**
 * Filter menu items to those the given role may access. A missing or
 * unknown role yields no items (nothing to show for an unsigned session).
 */
export function RoleMenuFilter(role: string | null, items: MenuItem[] = MENU_ITEMS): MenuItem[] {
  if (!role) return []
  return items.filter((item) => item.roles.includes(role as MenuRole))
}
