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
 */
import type { CostoTree as CostoTreeType } from '@/utils/productos'
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
        <el-table :data="group.lineas" size="small">
          <el-table-column prop="nombre" label="Concepto" min-width="200" />
          <el-table-column label="Cantidad" width="110" align="right">
            <template #default="{ row }">{{ formatQty(row.cantidad) }}</template>
          </el-table-column>
          <el-table-column label="Costo unitario" width="130" align="right">
            <template #default="{ row }">{{ formatMoney(row.costo_unitario) }}</template>
          </el-table-column>
          <el-table-column label="Costo total" width="130" align="right">
            <template #default="{ row }">{{ formatMoney(row.costo_total) }}</template>
          </el-table-column>
        </el-table>
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
  background: var(--el-color-primary-light-9);
  border-radius: 0.375rem;
}

.costo-total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--el-color-primary);
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
  color: var(--el-text-color-secondary);
  font-size: 0.875rem;
}

.costo-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.costo-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
