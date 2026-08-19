<script setup lang="ts">
/**
 * Role-aware sidebar navigation (task 1.7, spec SHELL-4/SHELL-5).
 *
 * Renders the menu items the current role may access (Usuarios is
 * admin-only) using the pure `RoleMenuFilter` from utils/menu — the same
 * roles the router guard enforces, so the visible menu can never offer a
 * route the role is blocked from.
 *
 * D3 (S3-T4): el-menu/el-menu-item are replaced by a flat `<nav>` +
 * `<router-link>` list; the active item is derived from `route.path` (exact
 * match against each item's top-level path).
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { RoleMenuFilter } from '@/utils/menu'

const route = useRoute()
const auth = useAuthStore()

/** Menu items visible to the current role (empty for an unsigned session). */
const items = computed(() => RoleMenuFilter(auth.role))

/** Exact-path match against the current route for active highlighting. */
function isActive(path: string): boolean {
  return route.path === path
}
</script>

<template>
  <nav class="sidebar-menu" aria-label="Navegación principal">
    <router-link
      v-for="item in items"
      :key="item.path"
      :to="item.path"
      class="sidebar-menu__item"
      :class="{ 'sidebar-menu__item--active': isActive(item.path) }"
    >
      {{ item.label }}
    </router-link>
  </nav>
</template>

<style scoped>
.sidebar-menu {
  display: flex;
  flex-direction: column;
  border-right: none;
}

.sidebar-menu__item {
  position: relative;
  padding: 0.75rem 1.25rem;
  font-family: var(--arpia-font-button);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.85);
  text-decoration: none;
}

.sidebar-menu__item:hover {
  color: #ffffff;
  background: rgba(140, 108, 161, 0.25);
}

.sidebar-menu__item--active {
  color: var(--arpia-primary-soft);
  background: rgba(140, 108, 161, 0.25);
}

.sidebar-menu__item--active::before {
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
