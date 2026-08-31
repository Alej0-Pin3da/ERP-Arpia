<script setup lang="ts">
defineProps<{
  isMock: boolean
  source: string
  count?: number
  endpoint?: string
}>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border tracking-wider"
    :class="isMock
      ? 'bg-amber-950/60 text-amber-300 border-amber-500/30'
      : 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30'"
    :title="isMock ? 'Datos en memoria (se pierden al F5)' : `Datos reales de ${endpoint ?? source}`"
  >
    <span class="w-1.5 h-1.5 rounded-full" :class="isMock ? 'bg-amber-400' : 'bg-emerald-400'" />
    {{ isMock ? 'MOCK' : 'REAL' }} — {{ source }}
    <span v-if="count !== undefined" class="opacity-80">· {{ count }}</span>
  </span>
</template>
