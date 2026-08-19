<script setup lang="ts">
/**
 * KPI cards (task 1.9, spec DASH-1).
 *
 * Four summary cards computed from the analytics endpoints: month sales
 * total + units (last row of ventas-mensuales), low-stock insumos count and
 * margen product count. All values go through the central es-CO formatters.
 */
import { computed } from 'vue'
import Card from 'primevue/card'
import Skeleton from 'primevue/skeleton'

import { formatMoney, formatQty } from '@/utils/format'

const props = defineProps<{
  /** Month total as Decimal-as-string (null when there are no sales). */
  monthTotal: string | null
  /** Units sold in the latest month (null when there are no sales). */
  monthCount: number | null
  /** Number of insumos below their minimum (insumos-bajo-stock length). */
  lowStockCount: number
  /** Number of products with computed margin (margen-por-producto length). */
  margenCount: number
  /** While true the cards show a skeleton instead of values. */
  loading?: boolean
}>()

const cards = computed(() => [
  { label: 'Ventas del mes', value: formatMoney(props.monthTotal) },
  { label: 'Unidades vendidas', value: formatQty(props.monthCount) },
  { label: 'Insumos bajo stock', value: formatQty(props.lowStockCount) },
  { label: 'Productos con margen', value: formatQty(props.margenCount) },
])
</script>

<template>
  <div class="kpi-cards">
    <div v-for="card in cards" :key="card.label" class="kpi-col">
      <Card :pt="{ root: { class: 'kpi-card' } }">
        <template #content>
          <p class="kpi-label">{{ card.label }}</p>
          <Skeleton v-if="loading" class="kpi-skeleton" />
          <p v-else class="kpi-value" data-test="kpi-value">{{ card.value }}</p>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.kpi-cards {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 1rem;
}

@media (min-width: 640px) {
  .kpi-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 768px) {
  .kpi-cards {
    grid-template-columns: repeat(4, 1fr);
  }
}

.kpi-card {
  border: 1px solid var(--arpia-border);
  border-radius: 0;
  background: var(--arpia-card);
  box-shadow: none;
}

.kpi-skeleton {
  width: 100%;
  height: 1.5rem;
}

.kpi-label {
  margin: 0 0 0.5rem;
  font-family: var(--arpia-font-heading);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--arpia-gold);
}

.kpi-value {
  margin: 0;
  font-family: var(--arpia-font-heading);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--arpia-primary-soft);
}
</style>