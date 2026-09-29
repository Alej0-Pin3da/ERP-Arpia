<script setup lang="ts">
import FinanzasSaldosTab from '@/components/finanzas/FinanzasSaldosTab.vue'
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-xl font-bold text-stone-100">Saldos en Vivo</h1>
      <p class="text-xs text-stone-400">Reparto por venta confirmada. Informativo — el cierre oficial sigue siendo la liquidación en Finanzas.</p>
    </div>

    <FinanzasSaldosTab />
  </div>
</template>
