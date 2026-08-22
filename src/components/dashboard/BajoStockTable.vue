<script setup lang="ts">
/**
 * Low-stock insumos table (DASH-2).
 *
 * Renders low stock insumos with severity tags and stock comparison.
 */
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
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

const SEVERITY_TAG: Record<Criticality, 'danger' | 'warn'> = {
  danger: 'danger',
  warning: 'warn',
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
  <DataTable :value="rows" lazy :loading="loading" :row-class="rowClass" class="custom-dashboard-table">
    <Column field="nombre" header="Insumo" style="min-width: 160px">
      <template #body="{ data }">
        <div class="insumo-cell">
          <i class="pi pi-box insumo-icon" />
          <span class="insumo-name">{{ data.nombre }}</span>
        </div>
      </template>
    </Column>
    <Column field="unidad_medida" header="Unidad" style="width: 90px">
      <template #body="{ data }">
        <span class="unit-badge">{{ data.unidad_medida }}</span>
      </template>
    </Column>
    <Column field="stock_actual" header="Stock Actual" style="width: 120px" align="right">
      <template #body="{ data }">
        <span class="stock-actual-val">{{ formatQty(data.stock_actual) }}</span>
      </template>
    </Column>
    <Column field="stock_minimo" header="Mínimo Requerido" style="width: 130px" align="right">
      <template #body="{ data }">
        <span class="stock-min-val">{{ formatQty(data.stock_minimo) }}</span>
      </template>
    </Column>
    <Column header="Estado" style="width: 110px" align="center">
      <template #body="{ data }">
        <Tag :severity="SEVERITY_TAG[criticalityOf(data)]" class="severity-pill">
          {{ SEVERITY_LABEL[criticalityOf(data)] }}
        </Tag>
      </template>
    </Column>

    <template #empty>
      <div class="bajo-stock-empty">
        <i class="pi pi-check-circle ok-icon" />
        <span>Todos los insumos se encuentran en niveles óptimos de stock</span>
      </div>
    </template>
  </DataTable>
</template>

<style scoped>
.custom-dashboard-table {
  border: none;
}

.insumo-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.insumo-icon {
  color: var(--arpia-primary);
  font-size: 0.85rem;
}

.insumo-name {
  font-weight: 600;
  color: var(--arpia-text-primary);
}

.unit-badge {
  font-size: 0.75rem;
  color: var(--arpia-text-muted);
  background: rgba(255, 255, 255, 0.05);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.stock-actual-val {
  font-weight: 700;
  color: var(--arpia-danger);
}

.stock-min-val {
  font-weight: 500;
  color: var(--arpia-text-muted);
}

.severity-pill {
  font-weight: 700;
  font-size: 0.72rem;
}

.bajo-stock-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--arpia-success);
  padding: 2.5rem 0;
  font-size: 0.88rem;
  font-weight: 500;
}

.ok-icon {
  font-size: 1.5rem;
}
</style>
