<script setup lang="ts">
/**
 * Low-stock insumos table (task 1.9, spec DASH-2).
 *
 * Renders /analiticos/insumos-bajo-stock rows with es-CO quantities and a
 * severity tag per row (every row is below its minimum by definition; how
 * far below decides Crítico vs Bajo). Row tint follows the same severity.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. el-tag cells stay until
 * slice 2b.
 */
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
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

/** DataTable row class hook — severity drives the row background tint. */
function rowClass(row: InsumoBajoStockRead): string {
  return stockSeverity(row.stock_actual, row.stock_minimo)
}
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading" :row-class="rowClass">
    <Column field="nombre" header="Insumo" style="min-width: 160px" />
    <Column field="unidad_medida" header="Unidad" style="width: 90px" />
    <Column field="stock_actual" header="Stock actual" style="width: 120px" align="right">
      <template #body="{ data }">{{ formatQty(data.stock_actual) }}</template>
    </Column>
    <Column field="stock_minimo" header="Stock mínimo" style="width: 120px" align="right">
      <template #body="{ data }">{{ formatQty(data.stock_minimo) }}</template>
    </Column>
    <Column header="Estado" style="width: 110px" align="center">
      <template #body="{ data }">
        <el-tag :type="SEVERITY_TAG[criticalityOf(data)]" size="small">
          {{ SEVERITY_LABEL[criticalityOf(data)] }}
        </el-tag>
      </template>
    </Column>

    <template #empty>
      <div class="bajo-stock-empty">Sin insumos bajo stock</div>
    </template>
  </DataTable>
</template>

<style scoped>
.bajo-stock-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
