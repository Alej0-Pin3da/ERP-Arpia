<script setup lang="ts">
/**
 * Persistent application layout (task 1.7, spec SHELL-5).
 *
 * The shell every authenticated route renders inside: a role-aware sidebar
 * (SidebarMenu), a header showing the logged user's nombre + rol with a
 * logout button, and a main area rendering the active route. Logout goes
 * through the auth store (POST /auth/logout + local session clear) and
 * returns to /login.
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import SidebarMenu from '@/components/layout/SidebarMenu.vue'
import { useAuthStore } from '@/stores/auth'
import { roleLabel } from '@/utils/menu'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

const auth = useAuthStore()
const router = useRouter()

/** es-CO role name for the header badge (Administrador/Operador/Consulta). */
const rolLabel = computed(() => roleLabel(auth.role))

async function onLogout(): Promise<void> {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="app-layout__aside">
      <div class="app-layout__brand">
        <span class="app-layout__brand-strong">ERP</span>
        <span class="app-layout__brand-accent">Arpia</span>
      </div>
      <SidebarMenu />
    </el-aside>

    <el-container class="app-layout__body">
      <el-header class="app-layout__header">
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
      </el-header>

      <el-main class="app-layout__main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.app-layout__aside {
  display: flex;
  flex-direction: column;
  background: var(--arpia-dark);
  border-right: 1px solid var(--arpia-border);
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
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  background: var(--arpia-bg-gradient);
}
</style>
