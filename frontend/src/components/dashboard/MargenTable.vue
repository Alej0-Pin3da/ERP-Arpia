<script setup lang="ts">
/**
 * Product margin table (task 1.9, spec DASH-3).
 *
 * Renders the client-side joined margen rows (buildMargenRows output):
 * product name, variant label (or '(base)'), total and average margin —
 * all Decimal-formatted es-CO. Missing products degrade to "Producto #{id}".
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c.
 */
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import { formatMoney } from '@/utils/format'
import type { MargenRow } from '@/utils/dashboard'

defineProps<{
  rows: MargenRow[]
  loading?: boolean
}>()
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading">
    <Column field="nombre" header="Producto" style="min-width: 180px" />
    <Column field="variante" header="Variante" style="min-width: 120px" />
    <Column field="margen_total" header="Margen total" style="width: 140px" align="right">
      <template #body="{ data }">{{ formatMoney(data.margen_total) }}</template>
    </Column>
    <Column field="margen_promedio" header="Margen promedio" style="width: 150px" align="right">
      <template #body="{ data }">{{ formatMoney(data.margen_promedio) }}</template>
    </Column>

    <template #empty>
      <div class="margen-empty">Sin márgenes calculados</div>
    </template>
  </DataTable>
</template>

<style scoped>
.margen-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>
