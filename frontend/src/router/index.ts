/**
 * Application router (task 1.6, spec SHELL-4).
 *
 * Route table with `meta.roles` (admin | operador | consulta) per spec:
 * `/login` public; `/dashboard` and the operational modules open to all roles
 * (write actions are gated in-view); `/usuarios` admin-only.
 *
 * Guard order (design "Guard order" + learning #5 — reload race):
 *   1. public route -> allow
 *   2. await `authStore.restoreIfNeeded()` — reconciles /auth/me from
 *      storage BEFORE any role decision (a fresh reload has an empty store;
 *      checking `meta.roles` first would bounce everyone to /dashboard)
 *   3. not authenticated -> /login?redirect=<fullPath>
 *   4. role not in `meta.roles` -> /dashboard
 *
 * The layout shell (AppLayout, PR4) wraps every authenticated route as a
 * child; `/login` stays standalone. View components for modules land in
 * PR5+ (RoutePlaceholder stands in until then).
 */
import { createRouter, createWebHistory, type RouteRecordRaw, type Router, type RouterHistory, type Component } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/layouts/AppLayout.vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import AnalisisView from '@/views/AnalisisView.vue'
import VentasView from '@/views/VentasView.vue'
import DevolucionesView from '@/views/DevolucionesView.vue'
import FinanzasView from '@/views/FinanzasView.vue'
import InventarioView from '@/views/InventarioView.vue'
import ProductosView from '@/views/ProductosView.vue'
import MaestrosView from '@/views/MaestrosView.vue'
import OmisionesView from '@/views/OmisionesView.vue'
import UsuariosView from '@/views/UsuariosView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    /** Route reachable without a session. */
    public?: boolean
    /** Roles allowed on this route. */
    roles?: string[]
  }
}

const ALL_ROLES = ['admin', 'operador', 'consulta']

// In test runner (jsdom), synchronous view resolution avoids microtask tick races.
// In development & production builds, dynamic imports enable route-level code splitting.
const lazy = (loader: () => Promise<Component>, sync: Component) =>
  import.meta.env.MODE === 'test' ? sync : loader

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  {
    // Authenticated shell: every authed route renders inside AppLayout
    // (header + role-aware sidebar + <router-view>). Child paths are
    // relative to the parent, so full paths stay /dashboard, /ventas, ...
    path: '/',
    component: AppLayout,
    children: [
      { path: '', redirect: '/dashboard' },
      // Dashboard is the default landing view inside AppLayout
      { path: 'dashboard', name: 'dashboard', component: DashboardView, meta: { roles: ALL_ROLES } },
      // Operational modules are code-split into on-demand lazy chunks:
      { path: 'analisis', name: 'analisis', component: lazy(() => import('@/views/AnalisisView.vue'), AnalisisView), meta: { roles: ALL_ROLES } },
      { path: 'ventas', name: 'ventas', component: lazy(() => import('@/views/VentasView.vue'), VentasView), meta: { roles: ALL_ROLES } },
      { path: 'devoluciones', name: 'devoluciones', component: lazy(() => import('@/views/DevolucionesView.vue'), DevolucionesView), meta: { roles: ALL_ROLES } },
      { path: 'finanzas', name: 'finanzas', component: lazy(() => import('@/views/FinanzasView.vue'), FinanzasView), meta: { roles: ALL_ROLES } },
      { path: 'inventario', name: 'inventario', component: lazy(() => import('@/views/InventarioView.vue'), InventarioView), meta: { roles: ALL_ROLES } },
      { path: 'productos', name: 'productos', component: lazy(() => import('@/views/ProductosView.vue'), ProductosView), meta: { roles: ALL_ROLES } },
      { path: 'maestros', name: 'maestros', component: lazy(() => import('@/views/MaestrosView.vue'), MaestrosView), meta: { roles: ALL_ROLES } },
      { path: 'omisiones', name: 'omisiones', component: lazy(() => import('@/views/OmisionesView.vue'), OmisionesView), meta: { roles: ALL_ROLES } },
      { path: 'usuarios', name: 'usuarios', component: lazy(() => import('@/views/UsuariosView.vue'), UsuariosView), meta: { roles: ['admin'] } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

/**
 * Create the router with the global auth guard attached. The `history`
 * parameter lets tests inject a memory history.
 */
export function createAppRouter(history: RouterHistory = createWebHistory()): Router {
  const router = createRouter({ history, routes })

  router.beforeEach(async (to) => {
    if (to.meta.public) {
      return true
    }

    // Restore BEFORE the role check — the store fast-paths when the session
    // was already restored (login flow), so this is cheap on navigation.
    const auth = useAuthStore()
    await auth.restoreIfNeeded()

    if (!auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    const roles = to.meta.roles
    if (roles && roles.length > 0 && !roles.includes(auth.role ?? '')) {
      return { name: 'dashboard' }
    }

    return true
  })

  return router
}

/** Singleton used by main.ts. */
export const router: Router = createAppRouter()
