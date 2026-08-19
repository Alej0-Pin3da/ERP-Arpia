<script setup lang="ts">
/**
 * Persistent application layout (task 1.7, spec SHELL-5).
 *
 * The shell every authenticated route renders inside: a role-aware sidebar
 * (SidebarMenu), a header showing the logged user's nombre + rol with a
 * logout button, and a main area rendering the active route. Logout goes
 * through the auth store (POST /auth/logout + local session clear) and
 * returns to /login.
 *
 * D3 (S3-T4): the el-container/el-header/el-aside/el-main wrapper trio is
 * replaced by a CSS grid shell — `.app-layout` `grid-template-areas` with a
 * fixed 220px aside column, an auto header row and a 1fr main row.
 */
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import SidebarMenu from '@/components/layout/SidebarMenu.vue'
import { useAuthStore } from '@/stores/auth'
import { roleLabel } from '@/utils/menu'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

const auth = useAuthStore()
const router = useRouter()
const sidebarOpen = ref(false)

/** es-CO role name for the header badge (Administrador/Operador/Consulta). */
const rolLabel = computed(() => roleLabel(auth.role))

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
    <button
      v-if="sidebarOpen"
      class="app-layout__scrim"
      type="button"
      aria-label="Cerrar menú"
      @click="closeSidebar"
    />

    <aside class="app-layout__aside" :class="{ 'app-layout__aside--open': sidebarOpen }">
      <div class="app-layout__brand">
        <span class="app-layout__brand-strong">ERP</span>
        <span class="app-layout__brand-accent">Arpia</span>
      </div>
      <SidebarMenu @click="closeSidebar" />
    </aside>

    <header class="app-layout__header">
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
      <div class="app-layout__user">
        <span class="app-layout__name">{{ auth.userName }}</span>
        <Tag class="app-layout__role" severity="secondary">{{ rolLabel }}</Tag>
      </div>
      <Button
        class="app-layout__logout"
        label="Cerrar sesión"
        severity="danger"
        outlined
        size="small"
        @click="onLogout"
      />
    </header>

    <main class="app-layout__main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas:
    'aside header'
    'aside main';
  min-height: 100vh;
}

.app-layout__aside {
  grid-area: aside;
  display: flex;
  flex-direction: column;
  background: var(--arpia-dark);
  border-right: 1px solid var(--arpia-border);
  z-index: 20;
}

.app-layout__scrim,
.app-layout__menu-toggle {
  display: none;
}

.app-layout__brand {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  padding: 1.25rem 1.25rem;
  font-family: var(--arpia-font-heading);
  font-weight: 600;
  font-size: 1.125rem;
}

.app-layout__brand-strong {
  color: var(--arpia-text-primary);
}

.app-layout__brand-accent {
  font-family: var(--arpia-font-heading);
  font-weight: 600;
  color: var(--arpia-gold);
}

.app-layout__header {
  grid-area: header;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.25rem;
  background: var(--arpia-dark-bg);
  border-bottom: 1px solid var(--arpia-border);
  backdrop-filter: blur(8px);
}

.app-layout__user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.app-layout__name {
  font-family: var(--arpia-font-heading);
  font-weight: 600;
  color: var(--arpia-text-primary);
}

.app-layout__main {
  grid-area: main;
  padding: 1.25rem;
  background: var(--arpia-bg-gradient);
  overflow: auto;
}

@media (max-width: 767px) {
  .app-layout {
    display: block;
  }

  .app-layout__aside {
    position: fixed;
    inset: 0 auto 0 0;
    width: min(84vw, 280px);
    transform: translateX(-100%);
    transition: transform 180ms ease;
    box-shadow: var(--arpia-shadow-deep);
  }

  .app-layout__aside--open {
    transform: translateX(0);
  }

  .app-layout__scrim {
    position: fixed;
    inset: 0;
    display: block;
    width: 100%;
    border: 0;
    background: var(--arpia-overlay);
    z-index: 10;
  }

  .app-layout__header {
    min-height: 4rem;
    padding: 0 0.75rem;
    gap: 0.5rem;
  }

  .app-layout__menu-toggle {
    display: inline-flex;
    flex: 0 0 auto;
  }

  .app-layout__user {
    min-width: 0;
    overflow: hidden;
  }

  .app-layout__name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .app-layout__logout :deep(.p-button-label) {
    display: none;
  }

  .app-layout__logout {
    flex: 0 0 auto;
  }

  .app-layout__main {
    min-height: calc(100dvh - 4rem);
    padding: 1rem 0.75rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-layout__aside,
  .sidebar-menu__item {
    transition: none;
  }
}
</style>
