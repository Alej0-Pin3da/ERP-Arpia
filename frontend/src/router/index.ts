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
import { createRouter, createWebHistory, type RouteRecordRaw, type Router, type RouterHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/layouts/AppLayout.vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import VentasView from '@/views/VentasView.vue'
import DevolucionesView from '@/views/DevolucionesView.vue'
import FinanzasView from '@/views/FinanzasView.vue'
import RoutePlaceholder from '@/views/RoutePlaceholder.vue'

declare module 'vue-router' {
  interface RouteMeta {
    /** Route reachable without a session. */
    public?: boolean
    /** Roles allowed on this route. */
    roles?: string[]
  }
}

const ALL_ROLES = ['admin', 'operador', 'consulta']

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
      // Dashboard landed in PR5; remaining modules keep the placeholder.
      { path: 'dashboard', name: 'dashboard', component: DashboardView, meta: { roles: ALL_ROLES } },
      { path: 'ventas', name: 'ventas', component: VentasView, meta: { roles: ALL_ROLES } },
      { path: 'devoluciones', name: 'devoluciones', component: DevolucionesView, meta: { roles: ALL_ROLES } },
      { path: 'finanzas', name: 'finanzas', component: FinanzasView, meta: { roles: ALL_ROLES } },
      { path: 'inventario', name: 'inventario', component: RoutePlaceholder, meta: { roles: ALL_ROLES } },
      { path: 'productos', name: 'productos', component: RoutePlaceholder, meta: { roles: ALL_ROLES } },
      { path: 'maestros', name: 'maestros', component: RoutePlaceholder, meta: { roles: ALL_ROLES } },
      { path: 'usuarios', name: 'usuarios', component: RoutePlaceholder, meta: { roles: ['admin'] } },
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
