<script setup lang="ts">
/**
 * Devoluciones list table (task 2.3, spec MOD-2).
 *
 * Renders the client-side joined rows (buildDevolucionRows output): es-CO
 * formatted fecha/monto, venta_id, tipo label with a colored tag (total
 * danger — cancels the sale; parcial warn), motivo (or an em dash), the
 * items count, and expandable item lines with the product name and the
 * sale-time snapshot subtotal. Missing products degrade to "Producto #{id}".
 *
 * Migrated to PrimeVue DataTable in slice 1b: the expander column opens the
 * `#expansion` nested DataTable (BEH-6 row expansion preserved). The Tag cell
 * was migrated in slice 2b.
 */
import { ref } from 'vue'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import { formatDateTime, formatMoney, formatQty } from '@/utils/format'
import { tipoLabel, tipoTagType, type DevolucionRow } from '@/utils/devoluciones'

defineProps<{
  rows: DevolucionRow[]
  loading?: boolean
}>()

/** Expanded rows keyed by row id (nested detail table). */
const expandedRows = ref<Record<string, boolean>>({})
</script>

<template>
  <DataTable
    :value="rows"
    v-model:expandedRows="expandedRows"
    dataKey="id"
    lazy
    :loading="loading"
  >
    <Column expander style="width: 3rem" />
    <template #expansion="{ data }">
      <DataTable :value="data.items" size="small" class="devolucion-detail-table">
        <Column field="nombre" header="Producto" style="min-width: 180px" />
        <Column header="Cantidad" style="width: 110px" align="right">
          <template #body="{ data: item }">{{ formatQty(item.cantidad) }}</template>
        </Column>
        <Column header="Subtotal" style="width: 130px" align="right">
          <template #body="{ data: item }">{{ formatMoney(item.subtotal) }}</template>
        </Column>
      </DataTable>
    </template>

    <Column field="id" header="#" style="width: 70px" />
    <Column field="fecha" header="Fecha" style="width: 110px">
      <template #body="{ data }">{{ formatDateTime(data.fecha) }}</template>
    </Column>
    <Column field="venta_id" header="Venta" style="width: 90px" align="right" />
    <Column header="Tipo" style="width: 110px">
      <template #body="{ data }">
        <Tag :severity="tipoTagType(data.tipo)">{{ tipoLabel(data.tipo) }}</Tag>
      </template>
    </Column>
    <Column field="motivo" header="Motivo" style="min-width: 220px" />
    <Column field="items.length" header="Items" style="width: 80px" align="right" />
    <Column header="Monto reembolsado" style="width: 170px" align="right">
      <template #body="{ data }">{{ formatMoney(data.monto_reembolsado) }}</template>
    </Column>

    <template #empty>
      <div class="devolucion-empty">Sin devoluciones registradas</div>
    </template>
  </DataTable>
</template>

<style scoped>
.devolucion-detail-table {
  padding: 0 1rem 0.5rem 3rem;
  background: var(--el-fill-color-lighter);
}

.devolucion-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
