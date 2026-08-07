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
</style>
