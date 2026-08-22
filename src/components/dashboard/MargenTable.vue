<script setup lang="ts">
/**
 * Product margin table (DASH-3).
 *
 * Renders product margins with currency formatting and margin status.
 */
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import { formatMoney } from '@/utils/format'
import type { MargenRow } from '@/utils/dashboard'

defineProps<{
  rows: MargenRow[]
  loading?: boolean
}>()
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading" class="custom-dashboard-table">
    <Column field="nombre" header="Producto" style="min-width: 180px">
      <template #body="{ data }">
        <div class="product-cell">
          <i class="pi pi-tag product-icon" />
          <span class="product-name">{{ data.nombre }}</span>
        </div>
      </template>
    </Column>
    <Column field="variante" header="Variante" style="min-width: 120px">
      <template #body="{ data }">
        <Tag severity="secondary" class="variant-tag">{{ data.variante }}</Tag>
      </template>
    </Column>
    <Column field="margen_total" header="Margen Total Acumulado" style="width: 180px" align="right">
      <template #body="{ data }">
        <span class="margin-total-val">{{ formatMoney(data.margen_total) }}</span>
      </template>
    </Column>
    <Column field="margen_promedio" header="Margen Promedio Unitario" style="width: 180px" align="right">
      <template #body="{ data }">
        <span class="margin-avg-val">{{ formatMoney(data.margen_promedio) }}</span>
      </template>
    </Column>

    <template #empty>
      <div class="margen-empty">
        <i class="pi pi-info-circle info-icon" />
        <span>Sin registros de márgenes calculados para el período</span>
      </div>
    </template>
  </DataTable>
</template>

<style scoped>
.custom-dashboard-table {
  border: none;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.product-icon {
  color: var(--arpia-primary);
  font-size: 0.85rem;
}

.product-name {
  font-weight: 600;
  color: var(--arpia-text-primary);
}

.variant-tag {
  font-size: 0.72rem;
  background: rgba(255, 255, 255, 0.06) !important;
  color: var(--arpia-text-regular) !important;
}

.margin-total-val {
  font-weight: 700;
  color: var(--arpia-success);
}

.margin-avg-val {
  font-weight: 600;
  color: var(--arpia-primary-soft);
}

.margen-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--arpia-text-muted);
  padding: 2.5rem 0;
  font-size: 0.88rem;
}

.info-icon {
  font-size: 1.5rem;
}
</style>
