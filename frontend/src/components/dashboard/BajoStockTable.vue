<script setup lang="ts">
/**
 * Low-stock insumos table (task 1.9, spec DASH-2).
 *
 * Renders /analiticos/insumos-bajo-stock rows with es-CO quantities and a
 * severity tag per row (every row is below its minimum by definition; how
 * far below decides Crítico vs Bajo). Row tint follows the same severity.
 */
import { formatQty } from '@/utils/format'
import { stockSeverity, type StockSeverity } from '@/utils/dashboard'
import type { InsumoBajoStockRead } from '@/types/api.d'

defineProps<{
  rows: InsumoBajoStockRead[]
  loading?: boolean
}>()

type Criticality = Exclude<StockSeverity, 'ok'>

const SEVERITY_LABEL: Record<Criticality, string> = {
  danger: 'Crítico',
  warning: 'Bajo',
}

const SEVERITY_TAG: Record<Criticality, 'danger' | 'warning'> = {
  danger: 'danger',
  warning: 'warning',
}

function criticalityOf(row: InsumoBajoStockRead): Criticality {
  return stockSeverity(row.stock_actual, row.stock_minimo) as Criticality
}

/** el-table row class hook — severity drives the row background tint. */
function rowClass({ row }: { row: InsumoBajoStockRead }): string {
  return stockSeverity(row.stock_actual, row.stock_minimo)
}
</script>

<template>
  <el-table :data="rows" :row-class-name="rowClass" v-loading="loading">
    <el-table-column prop="nombre" label="Insumo" min-width="160" />
    <el-table-column prop="unidad_medida" label="Unidad" width="90" />
    <el-table-column label="Stock actual" width="120" align="right">
      <template #default="{ row }">{{ formatQty(row.stock_actual) }}</template>
    </el-table-column>
    <el-table-column label="Stock mínimo" width="120" align="right">
      <template #default="{ row }">{{ formatQty(row.stock_minimo) }}</template>
    </el-table-column>
    <el-table-column label="Estado" width="110" align="center">
      <template #default="{ row }">
        <el-tag :type="SEVERITY_TAG[criticalityOf(row)]" size="small">
          {{ SEVERITY_LABEL[criticalityOf(row)] }}
        </el-tag>
      </template>
    </el-table-column>
    <template #empty>
      <el-empty description="Sin insumos bajo stock" :image-size="80" />
    </template>
  </el-table>
</template>
