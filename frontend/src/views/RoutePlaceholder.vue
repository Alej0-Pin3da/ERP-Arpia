<script setup lang="ts">
/**
 * Route placeholder — stands in for views that land in later PRs
 * (layout shell PR4, dashboard PR5, module views PR6+). Shows the route
 * name so navigation is visibly wired before the real screens exist.
 */
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <section class="route-placeholder">
    <h2>{{ route.name }}</h2>
    <p>Módulo en construcción — se reemplaza en los PRs siguientes (frontend-dashboard).</p>
  </section>
</template>

<style scoped>
.route-placeholder {
  padding: 2rem;
  color: #6b7280;
  text-align: center;
}

.route-placeholder h2 {
  text-transform: capitalize;
}
</style>
