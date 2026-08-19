<script setup lang="ts">
/**
 * Combo contents (BomProducto) table (PR10, spec MOD-5).
 *
 * Lists the BOM producto lines of the selected product (what else goes into
 * the combo). Rows arrive already joined (included product name from
 * buildBomProductoRows); cantidad renders es-CO. NOTE: the backend
 * BomProducto schema has NO desperdicio field — only producto_incluido_id +
 * cantidad (verified backend schemas/bom.py). Editar/Eliminar are admin-only.
 *
 * Presentational: emits `edit` / `delete` with the clicked row.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. Button cells were
 * migrated in slice 2b.
 */
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import type { BomProductoRow } from '@/utils/productos'
import { formatQty } from '@/utils/format'

defineProps<{
  rows: BomProductoRow[]
  loading: boolean
  canEdit: boolean
}>()

defineEmits<{
  edit: [row: BomProductoRow]
  delete: [row: BomProductoRow]
}>()
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading">
    <Column field="producto" header="Producto incluido" style="min-width: 220px" />
    <Column field="cantidad" header="Cantidad" style="width: 140px" align="right">
      <template #body="{ data }">{{ formatQty(data.cantidad) }}</template>
    </Column>
    <Column v-if="canEdit" header="Acciones" style="width: 180px">
      <template #body="{ data: row }">
        <Button size="small" severity="secondary" data-test="edit-bom-producto" @click="$emit('edit', row)">Editar</Button>
        <Button size="small" severity="danger" data-test="delete-bom-producto" @click="$emit('delete', row)">
          Eliminar
        </Button>
      </template>
    </Column>

    <template #empty>
      <div class="bom-producto-empty">Sin productos en el combo</div>
    </template>
  </DataTable>
</template>

<style scoped>
.bom-producto-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
