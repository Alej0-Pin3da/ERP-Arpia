<script setup lang="ts">
/**
 * Persistent Enterprise Atelier Layout.
 *
 * Implements Arpía (arpia.com.co) luxury aesthetic:
 * - Golden Arpía Atelier emblem with refined Cinzel typography
 * - Clean Noir and Gold sidebar with categorized luxury navigation
 * - Atelier status chip ("Taller Activo • Pereira, Colombia")
 * - Role-aware access and top-bar actions
 */
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SidebarMenu from '@/components/layout/SidebarMenu.vue'
import AsistenteIaModal from '@/components/atelier/AsistenteIaModal.vue'
import NotificacionesModal from '@/components/atelier/NotificacionesModal.vue'
import { useAuthStore } from '@/stores/auth'
import { useAtelierStore } from '@/stores/atelier'
import { roleLabel } from '@/utils/menu'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

const auth = useAuthStore()
const atelier = useAtelierStore()
const router = useRouter()
const route = useRoute()
const sidebarOpen = ref(false)
const showIaModal = ref(false)
const showNotifModal = ref(false)

/** es-CO role name for the header badge (Administrador/Operador/Consulta). */
const rolLabel = computed(() => roleLabel(auth.role))

const routeTitle = computed(() => {
  const map: Record<string, string> = {
    dashboard: 'Panel General de Operaciones',
    produccion: 'Gestión de Pedidos & Confección',
    inventario: 'Inventario de Insumos & Telas',
    insumos: 'Inventario de Insumos & Telas',
    productos: 'Recetas de Confección & Fichas BOM',
    recetas: 'Recetas de Confección & Fichas BOM',
    prendas: 'Perchero & Prendas Confeccionadas',
    clientes: 'Gestión de Clientes & Medidas (CRM)',
    cotizador: 'Cotizador Rápido de Costura',
    optimizador: 'Optimizador Textil & Retazos',
    analisis: 'Análisis & Rentabilidad',
    ventas: 'Ventas Realizadas',
    devoluciones: 'Garantías & Devoluciones',
    finanzas: 'Reparto de Utilidades (Socias)',
    socias: 'Reparto de Utilidades (Socias)',
    maestros: 'Catálogos Maestros',
    omisiones: 'Bitácora de Omisiones',
    usuarios: 'Gestión de Usuarios & Roles',
  }
  const name = String(route.name || '')
  return map[name] || 'Atelier Arpía'
})

const userInitials = computed(() => {
  const name = auth.userName || 'Usuario'
  const parts = name.split(' ').filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
})

async function onLogout(): Promise<void> {
  sidebarOpen.value = false
  await auth.logout()
  router.push({ name: 'login' })
}

function closeSidebar(): void {
  sidebarOpen.value = false
}
</script>

<template>
  <div class="app-layout">
    <!-- Backdrop scrim for mobile sidebar -->
    <button
      v-if="sidebarOpen"
      class="app-layout__scrim"
      type="button"
      aria-label="Cerrar menú"
      @click="closeSidebar"
    />

    <!-- Sidebar Navigation -->
    <aside class="app-layout__aside" :class="{ 'app-layout__aside--open': sidebarOpen }">
      <div class="app-layout__brand">
        <div class="brand-logo-emblem">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" class="brand-svg">
            <path d="M16 2L5 8V16C5 22.8 9.7 29.2 16 31C22.3 29.2 27 22.8 27 16V8L16 2Z" fill="url(#layout-gold-bg)" fill-opacity="0.25" stroke="url(#layout-gold)" stroke-width="1.6" />
            <path d="M16 6L11 12H14V22H18V12H21L16 6Z" fill="url(#layout-gold)" />
            <path d="M11 15L7 18M21 15L25 18M11 19L8 22M21 19L24 22" stroke="url(#layout-gold)" stroke-width="1.3" stroke-linecap="round" />
            <defs>
              <linearGradient id="layout-gold" x1="5" y1="2" x2="27" y2="31" gradientUnits="userSpaceOnUse">
                <stop stop-color="#F3E5AB" />
                <stop offset="0.5" stop-color="#C5A059" />
                <stop offset="1" stop-color="#DFB15B" />
              </linearGradient>
              <linearGradient id="layout-gold-bg" x1="5" y1="2" x2="27" y2="31" gradientUnits="userSpaceOnUse">
                <stop stop-color="#DFB15B" stop-opacity="0.3" />
                <stop offset="1" stop-color="#9E7D3B" stop-opacity="0.05" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div class="brand-text-block">
          <div class="brand-title">
            <span class="brand-arpia-title">ARPÍA</span>
          </div>
          <span class="brand-subtitle">Atelier de Alta Costura</span>
        </div>
      </div>

      <div class="sidebar-scroll-area">
        <SidebarMenu @click="closeSidebar" />
      </div>

      <!-- Bottom User Profile Card -->
      <div class="sidebar-user-footer">
        <div class="user-avatar-badge">{{ userInitials }}</div>
        <div class="user-details">
          <div class="user-name-line">
            <span class="app-layout__name">{{ auth.userName }}</span>
            <span class="user-status-dot" title="Taller En Línea"></span>
          </div>
          <span class="user-email-text">{{ auth.user?.email || 'admin@arpia.com' }}</span>
        </div>
      </div>
    </aside>

    <!-- Top Navigation Header -->
    <header class="app-layout__header">
      <div class="header-left">
        <Button
          class="app-layout__menu-toggle"
          icon="pi pi-bars"
          text
          rounded
          aria-label="Abrir menú"
          :aria-expanded="sidebarOpen"
          aria-controls="app-navigation"
          @click="sidebarOpen = true"
        />

        <div class="breadcrumbs-block">
          <span class="breadcrumb-root">ARPÍA ERP</span>
          <i class="pi pi-chevron-right breadcrumb-separator" />
          <span class="breadcrumb-current">{{ routeTitle }}</span>
        </div>
      </div>

      <div class="header-right">
        <!-- AI Assistant Fast Trigger -->
        <Button
          label="Asistente IA"
          icon="pi pi-sparkles"
          size="small"
          class="p-button-warning text-xs font-semibold hidden sm:inline-flex"
          @click="showIaModal = true"
        />

        <!-- Notifications button with alert badge -->
        <button
          type="button"
          class="relative p-2 text-stone-400 hover:text-amber-400 rounded-lg transition hover:bg-stone-900"
          title="Notificaciones de taller"
          @click="showNotifModal = true"
        >
          <i class="pi pi-bell text-sm" />
          <span
            v-if="atelier.insumosCriticos.length"
            class="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500 ring-2 ring-stone-950"
          />
        </button>

        <!-- Live System Status Badge -->
        <div class="system-status-chip">
          <span class="pulse-indicator"></span>
          <span class="status-chip-text">Taller Pereira • Activo</span>
        </div>

        <div class="app-layout__user">
          <Tag class="app-layout__role" severity="secondary">{{ rolLabel }}</Tag>
        </div>

        <Button
          class="app-layout__logout"
          label="Salir"
          icon="pi pi-sign-out"
          severity="danger"
          outlined
          size="small"
          @click="onLogout"
        />
      </div>
    </header>

    <!-- Main Content Viewport -->
    <main class="app-layout__main">
      <div class="main-content-wrapper">
        <router-view />
      </div>
    </main>

    <!-- Global Atelier Modals -->
    <AsistenteIaModal v-model:visible="showIaModal" />
    <NotificacionesModal v-model:visible="showNotifModal" @ir-insumos="router.push('/insumos')" />
  </div>
</template>

<style scoped>
.app-layout {
  display: grid;
  grid-template-columns: 268px 1fr;
  grid-template-rows: 64px 1fr;
  grid-template-areas:
    'aside header'
    'aside main';
  min-height: 100vh;
  background-color: var(--arpia-dark-bg);
}

.app-layout__aside {
  grid-area: aside;
  display: flex;
  flex-direction: column;
  background: #0d0d11;
  border-right: 1px solid rgba(197, 160, 89, 0.15);
  z-index: 30;
  position: sticky;
  top: 0;
  height: 100vh;
}

.app-layout__scrim,
.app-layout__menu-toggle {
  display: none;
}

.app-layout__brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 1.2rem 1.25rem;
  border-bottom: 1px solid rgba(197, 160, 89, 0.15);
  background: linear-gradient(180deg, rgba(197, 160, 89, 0.06) 0%, transparent 100%);
}

.brand-logo-emblem {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(197, 160, 89, 0.08);
  border: 1px solid rgba(197, 160, 89, 0.3);
  box-shadow: 0 0 15px rgba(197, 160, 89, 0.15);
}

.brand-svg {
  width: 24px;
  height: 24px;
}

.brand-text-block {
  display: flex;
  flex-direction: column;
}

.brand-title {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.brand-arpia-title {
  font-family: var(--arpia-font-display);
  font-weight: 800;
  font-size: 1.25rem;
  letter-spacing: 0.16em;
  background: var(--arpia-gold-text);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-subtitle {
  font-family: var(--arpia-font-serif);
  font-style: italic;
  font-size: 0.76rem;
  color: var(--arpia-text-muted);
  letter-spacing: 0.02em;
}

.sidebar-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 0.85rem 0.65rem;
}

.sidebar-user-footer {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1.1rem;
  border-top: 1px solid rgba(197, 160, 89, 0.15);
  background: #111116;
}

.user-avatar-badge {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #c5a059 0%, #9e7d3b 100%);
  color: #09090b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--arpia-font-heading);
  font-weight: 800;
  font-size: 0.8rem;
  box-shadow: 0 2px 10px rgba(197, 160, 89, 0.25);
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name-line {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.app-layout__name {
  font-family: var(--arpia-font-heading);
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--arpia-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--arpia-gold);
  box-shadow: 0 0 6px var(--arpia-gold);
  flex-shrink: 0;
}

.user-email-text {
  font-size: 0.7rem;
  color: var(--arpia-text-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Header */
.app-layout__header {
  grid-area: header;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.75rem;
  background: rgba(13, 13, 17, 0.85);
  border-bottom: 1px solid rgba(197, 160, 89, 0.15);
  backdrop-filter: blur(16px);
  position: sticky;
  top: 0;
  z-index: 20;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.breadcrumbs-block {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.breadcrumb-root {
  font-family: var(--arpia-font-heading);
  font-weight: 600;
  font-size: 0.8rem;
  letter-spacing: 0.05em;
  color: var(--arpia-primary);
}

.breadcrumb-separator {
  font-size: 0.7rem;
  color: var(--arpia-text-faint);
}

.breadcrumb-current {
  font-family: var(--arpia-font-heading);
  font-weight: 700;
  color: var(--arpia-text-primary);
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.system-status-chip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.85rem;
  background: rgba(197, 160, 89, 0.06);
  border: 1px solid rgba(197, 160, 89, 0.25);
  border-radius: 9999px;
}

.pulse-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--arpia-gold);
  box-shadow: 0 0 8px var(--arpia-gold);
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.status-chip-text {
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--arpia-gold-soft);
  letter-spacing: 0.02em;
}

.app-layout__user {
  display: flex;
  align-items: center;
}

.app-layout__role {
  background: rgba(197, 160, 89, 0.12) !important;
  color: var(--arpia-primary-soft) !important;
  border: 1px solid rgba(197, 160, 89, 0.3) !important;
  font-weight: 700 !important;
}

.app-layout__logout {
  font-size: 0.78rem;
  padding: 0.35rem 0.75rem;
  border-color: rgba(225, 29, 72, 0.4) !important;
}

.app-layout__logout:hover {
  background: rgba(225, 29, 72, 0.15) !important;
}

/* Main Area */
.app-layout__main {
  grid-area: main;
  overflow-y: auto;
  padding: 1.5rem 1.75rem 2.5rem;
  background-color: transparent;
}

.main-content-wrapper {
  max-width: 1440px;
  margin: 0 auto;
}

/* Responsive Mobile Rules */
@media (max-width: 992px) {
  .app-layout {
    grid-template-columns: 1fr;
    grid-template-areas:
      'header'
      'main';
  }

  .app-layout__aside {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 268px;
    transform: translateX(-100%);
    transition: transform 240ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .app-layout__aside--open {
    transform: translateX(0);
    box-shadow: var(--arpia-shadow-deep);
  }

  .app-layout__scrim {
    display: block;
    position: fixed;
    inset: 0;
    background: var(--arpia-overlay);
    backdrop-filter: blur(4px);
    z-index: 25;
    border: none;
    cursor: pointer;
  }

  .app-layout__menu-toggle {
    display: inline-flex;
    color: var(--arpia-primary);
  }

  .system-status-chip {
    display: none;
  }

  .app-layout__main {
    padding: 1rem 1rem 2rem;
  }
}
</style>
