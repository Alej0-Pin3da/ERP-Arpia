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
      <div class="app-layout__brand">ERP Arpia</div>
      <SidebarMenu />
    </el-aside>

    <el-container class="app-layout__body">
      <el-header class="app-layout__header">
        <div class="app-layout__user">
          <span class="app-layout__name">{{ auth.userName }}</span>
          <el-tag size="small" class="app-layout__role">{{ rolLabel }}</el-tag>
        </div>
        <el-button class="app-layout__logout" type="danger" plain size="small" @click="onLogout">
          Cerrar sesión
        </el-button>
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
  border-right: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.app-layout__brand {
  padding: 1rem 1.25rem;
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--el-color-primary);
}

.app-layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.app-layout__user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.app-layout__main {
  background: var(--el-fill-color-blank);
}
</style>
