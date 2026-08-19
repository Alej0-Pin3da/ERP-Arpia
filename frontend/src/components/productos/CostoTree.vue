<script setup lang="ts">
/**
 * Cost breakdown tree (PR10, spec MOD-5).
 *
 * Renders the CostoProduccionRead tree pre-grouped by buildCostoTree: one
 * section per tipo present (Insumos / Productos / Costos operativos fijos),
 * each with its lineas (nombre, cantidad es-CO, costo_unitario es-CO,
 * costo_total es-CO), the group subtotal, and the grand total on top.
 *
 * Presentational: the view owns GET /productos/{id}/costo?variante_id and
 * passes the mapped tree.
 *
 * Migrated to PrimeVue DataTable (plain value mode) in slice 5 (MIG-2):
 * size small keeps the compact EP look; the formatted cells use the
 * Column #body slot with the same es-CO formatters.
 */
import type { CostoTree as CostoTreeType } from '@/utils/productos'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Skeleton from 'primevue/skeleton'
import { formatMoney, formatQty } from '@/utils/format'

defineProps<{
  tree: CostoTreeType | null
  loading: boolean
}>()
</script>

<template>
  <div>
    <div v-if="loading" class="costo-skeleton" data-test="costo-loading">
      <Skeleton v-for="n in 3" :key="n" />
    </div>
    <template v-else>
    <template v-if="tree && tree.groups.length > 0">
      <div class="costo-total" data-test="costo-total">
        <strong>Costo total de producción:</strong>
        <span class="costo-total-value">{{ formatMoney(tree.total) }}</span>
      </div>

      <section v-for="group in tree.groups" :key="group.tipo" class="costo-group">
        <header class="costo-group-header">
          <h4>{{ group.label }}</h4>
          <span class="costo-group-subtotal" data-test="costo-subtotal">
            Subtotal: {{ formatMoney(group.subtotal) }}
          </span>
        </header>
        <DataTable :value="group.lineas" size="small">
          <Column field="nombre" header="Concepto" style="min-width: 200px" />
          <Column header="Cantidad" style="width: 110px" align="right">
            <template #body="{ data }">{{ formatQty(data.cantidad) }}</template>
          </Column>
          <Column header="Costo unitario" style="width: 130px" align="right">
            <template #body="{ data }">{{ formatMoney(data.costo_unitario) }}</template>
          </Column>
          <Column header="Costo total" style="width: 130px" align="right">
            <template #body="{ data }">{{ formatMoney(data.costo_total) }}</template>
          </Column>
        </DataTable>
      </section>
    </template>
    <div v-else-if="tree" class="costo-empty">El producto no tiene costos desglosables</div>
    </template>
  </div>
</template>

<style scoped>
.costo-total {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: color-mix(in srgb, var(--arpia-primary-deep) 13%, transparent);
  border-radius: 0.375rem;
}

.costo-total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--arpia-primary);
}

.costo-group {
  margin-bottom: 1.25rem;
}

.costo-group-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.costo-group-header h4 {
  margin: 0;
}

.costo-group-subtotal {
  color: var(--arpia-text-muted);
  font-size: 0.875rem;
}

.costo-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.costo-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>
