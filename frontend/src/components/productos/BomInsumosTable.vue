<script setup lang="ts">
/**
 * BOM insumo lines table (PR10, spec MOD-5).
 *
 * Lists the BOM insumo lines of the selected product. Rows arrive already
 * joined (insumo name + unidad_medida from buildBomInsumoRows); cantidad is
 * es-CO qty and desperdicio renders as a % (0%..100%). Editar/Eliminar are
 * admin-only via `canEdit`.
 *
 * Presentational: emits `edit` / `delete` with the clicked row.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. Button cells were
 * migrated in slice 2b.
 */
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import type { BomInsumoRow } from '@/utils/productos'
import { formatQty } from '@/utils/format'

defineProps<{
  rows: BomInsumoRow[]
  loading: boolean
  canEdit: boolean
}>()

defineEmits<{
  edit: [row: BomInsumoRow]
  delete: [row: BomInsumoRow]
}>()
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading">
    <Column field="insumo" header="Insumo" style="min-width: 180px" />
    <Column field="unidad_medida" header="Unidad" style="width: 100px" />
    <Column field="cantidad_requerida" header="Cantidad requerida" style="width: 150px" align="right">
      <template #body="{ data }">{{ formatQty(data.cantidad_requerida) }}</template>
    </Column>
    <Column field="porcentaje_desperdicio" header="Desperdicio" style="width: 120px" align="right">
      <template #body="{ data }">{{ formatQty(data.porcentaje_desperdicio) }} %</template>
    </Column>
    <Column v-if="canEdit" header="Acciones" style="width: 180px">
      <template #body="{ data: row }">
        <Button size="small" severity="secondary" data-test="edit-bom-insumo" @click="$emit('edit', row)">Editar</Button>
        <Button size="small" severity="danger" data-test="delete-bom-insumo" @click="$emit('delete', row)">
          Eliminar
        </Button>
      </template>
    </Column>

    <template #empty>
      <div class="bom-insumo-empty">Sin insumos en la receta</div>
    </template>
  </DataTable>
</template>

<style scoped>
.bom-insumo-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>
