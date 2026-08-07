<script setup lang="ts">
/**
 * Product margin table (task 1.9, spec DASH-3).
 *
 * Renders the client-side joined margen rows (buildMargenRows output):
 * product name, variant label (or '(base)'), total and average margin —
 * all Decimal-formatted es-CO. Missing products degrade to "Producto #{id}".
 */
import { formatMoney } from '@/utils/format'
import type { MargenRow } from '@/utils/dashboard'

defineProps<{
  rows: MargenRow[]
  loading?: boolean
}>()
</script>

<template>
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="nombre" label="Producto" min-width="180" />
    <el-table-column prop="variante" label="Variante" min-width="120" />
    <el-table-column label="Margen total" width="140" align="right">
      <template #default="{ row }">{{ formatMoney(row.margen_total) }}</template>
    </el-table-column>
    <el-table-column label="Margen promedio" width="150" align="right">
      <template #default="{ row }">{{ formatMoney(row.margen_promedio) }}</template>
    </el-table-column>
    <template #empty>
      <el-empty description="Sin márgenes calculados" :image-size="80" />
    </template>
  </el-table>
</template>
