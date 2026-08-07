<script setup lang="ts">
const appName = 'ERP Arpia'
</script>

<template>
  <main class="app-shell">
    <h1>{{ appName }}</h1>
    <p class="tagline">Frontend scaffold — Phase 6 (frontend-dashboard)</p>
    <p class="hint">Slices siguientes: API client, auth, layout y módulos.</p>
  </main>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  font-family: 'Segoe UI', system-ui, sans-serif;
  color: #1f2937;
}

h1 {
  margin: 0 0 0.25rem;
  font-size: 2.5rem;
}

.tagline {
  margin: 0 0 1rem;
  font-size: 1.1rem;
  color: #6b7280;
}

.hint {
  font-size: 0.9rem;
  color: #9ca3af;
}
</style>
