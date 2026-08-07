<script setup lang="ts">
/**
 * KPI cards (task 1.9, spec DASH-1).
 *
 * Four summary cards computed from the analytics endpoints: month sales
 * total + units (last row of ventas-mensuales), low-stock insumos count and
 * margen product count. All values go through the central es-CO formatters.
 */
import { computed } from 'vue'

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
  <el-row :gutter="16" class="kpi-cards">
    <el-col v-for="card in cards" :key="card.label" :xs="24" :sm="12" :md="6">
      <el-card shadow="never" class="kpi-card">
        <p class="kpi-label">{{ card.label }}</p>
        <el-skeleton v-if="loading" :rows="1" animated />
        <p v-else class="kpi-value" data-test="kpi-value">{{ card.value }}</p>
      </el-card>
    </el-col>
  </el-row>
</template>

<style scoped>
.kpi-card {
  margin-bottom: 1rem;
}

.kpi-label {
  margin: 0 0 0.5rem;
  color: #606266;
  font-size: 0.85rem;
}

.kpi-value {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-color-primary);
}
</style>
