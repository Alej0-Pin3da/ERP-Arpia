<script setup lang="ts">
/**
 * Role-aware sidebar navigation (task 1.7, spec SHELL-4/SHELL-5).
 *
 * Renders the menu items the current role may access (Usuarios is
 * admin-only) using the pure `RoleMenuFilter` from utils/menu — the same
 * roles the router guard enforces, so the visible menu can never offer a
 * route the role is blocked from. ElMenu runs in router mode: each item's
 * `index` is its route path (click navigates) and `default-active` follows
 * the current route for highlighting.
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { RoleMenuFilter } from '@/utils/menu'

const route = useRoute()
const auth = useAuthStore()

/** Menu items visible to the current role (empty for an unsigned session). */
const items = computed(() => RoleMenuFilter(auth.role))
</script>

<template>
  <el-menu class="sidebar-menu" :default-active="route.path" router>
    <el-menu-item v-for="item in items" :key="item.path" :index="item.path">
      {{ item.label }}
    </el-menu-item>
  </el-menu>
</template>

<style scoped>
.sidebar-menu {
  border-right: none;
}

.sidebar-menu :deep(.el-menu-item) {
  position: relative;
  font-family: var(--arpia-font-button);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.85);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  color: #ffffff;
  background: rgba(140, 108, 161, 0.25);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  color: var(--arpia-primary-soft);
  background: rgba(140, 108, 161, 0.25);
}

.sidebar-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 20%;
  bottom: 20%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--arpia-brand-gradient);
}
</style>
