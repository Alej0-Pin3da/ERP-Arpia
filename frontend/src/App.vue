<script setup lang="ts">
/**
 * SPA shell — renders the active route through <router-view>.
 * The persistent layout (header + role-aware sidebar) is AppLayout (PR4);
 * the router wraps every authenticated route as its child, so /login stays
 * standalone and everything else renders inside the shell.
 */
</script>

<template>
  <router-view />
</template>
