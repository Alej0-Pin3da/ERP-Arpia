<script setup lang="ts">
// DataSourceBadge — REAL-only static badge (FastAPI + Postgres).
defineProps<{
  source: string
  count?: number
  endpoint?: string
}>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border tracking-wider bg-emerald-950/60 text-emerald-300 border-emerald-500/30"
    :title="`Datos reales de ${endpoint ?? source}`"
  >
    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400" />
    REAL — {{ source }}
    <span v-if="count !== undefined" class="opacity-80">· {{ count }}</span>
  </span>
</template>
