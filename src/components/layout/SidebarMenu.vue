<script setup lang="ts">
/**
 * Role-aware sidebar navigation (SHELL-4/SHELL-5).
 *
 * Renders filtered menu items based on current authenticated role.
 * Structured with modern pill-style links, sleek icons, glowing active state,
 * and high-contrast accessibility.
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { RoleMenuFilter } from '@/utils/menu'

const route = useRoute()
const auth = useAuthStore()

/** Menu items visible to the current role */
const items = computed(() => RoleMenuFilter(auth.role))

/** Exact or prefix path match against current route for active highlighting */
function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(`${path}/`)
}

// Section grouping helper
function getItemCategory(name: string): string {
  if (['dashboard', 'analisis'].includes(name)) return 'PANEL & ANALÍTICA'
  if (['ventas', 'devoluciones', 'finanzas'].includes(name)) return 'GESTIÓN COMERCIAL'
  if (['inventario', 'productos'].includes(name)) return 'TALLER & CATÁLOGO'
  return 'SISTEMA & CONTROL'
}

const categorizedItems = computed(() => {
  const groups: { category: string; items: typeof items.value }[] = []
  const seenCategories = new Set<string>()

  for (const item of items.value) {
    const cat = getItemCategory(item.name)
    if (!seenCategories.has(cat)) {
      seenCategories.add(cat)
      groups.push({ category: cat, items: [] })
    }
    const group = groups.find((g) => g.category === cat)
    if (group) group.items.push(item)
  }
  return groups
})
</script>

<template>
  <nav id="app-navigation" class="sidebar-menu" aria-label="Navegación principal">
    <div v-for="group in categorizedItems" :key="group.category" class="menu-group">
      <div class="menu-group-header">{{ group.category }}</div>
      <router-link
        v-for="item in group.items"
        :key="item.path"
        :to="item.path"
        class="sidebar-menu__item"
        :class="{ 'sidebar-menu__item--active': isActive(item.path) }"
      >
        <div class="item-icon-box">
          <i :class="['pi', item.icon]" aria-hidden="true" />
        </div>
        <span class="item-label">{{ item.label }}</span>
        <i v-if="isActive(item.path)" class="pi pi-chevron-right active-indicator-arrow" />
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.menu-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.menu-group-header {
  font-family: var(--arpia-font-heading);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--arpia-primary);
  opacity: 0.85;
  padding: 0.25rem 0.85rem;
}

.sidebar-menu__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.85rem;
  border-radius: var(--arpia-radius);
  font-family: var(--arpia-font-button);
  font-weight: 500;
  font-size: 0.84rem;
  color: var(--arpia-text-regular);
  text-decoration: none;
  transition: all 180ms ease;
  border: 1px solid transparent;
}

.sidebar-menu__item:hover {
  color: #fafaf9;
  background: rgba(197, 160, 89, 0.08);
  border-color: rgba(197, 160, 89, 0.15);
}

.sidebar-menu__item:focus-visible {
  outline: 2px solid var(--arpia-primary);
  outline-offset: 1px;
}

.item-icon-box {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--arpia-text-muted);
  transition: all 180ms ease;
  flex-shrink: 0;
}

.sidebar-menu__item:hover .item-icon-box {
  color: var(--arpia-primary-soft);
  background: rgba(197, 160, 89, 0.12);
}

.item-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.active-indicator-arrow {
  font-size: 0.65rem;
  color: var(--arpia-primary);
}

.sidebar-menu__item--active {
  color: #ffffff !important;
  font-weight: 700;
  background: linear-gradient(90deg, rgba(197, 160, 89, 0.18) 0%, rgba(197, 160, 89, 0.04) 100%) !important;
  border-color: rgba(197, 160, 89, 0.35) !important;
  box-shadow: 0 0 15px rgba(197, 160, 89, 0.1);
}

.sidebar-menu__item--active .item-icon-box {
  background: var(--arpia-primary);
  color: #09090b;
  box-shadow: 0 0 10px rgba(197, 160, 89, 0.4);
}

.sidebar-menu__item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 15%;
  bottom: 15%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--arpia-gold);
}
</style>
