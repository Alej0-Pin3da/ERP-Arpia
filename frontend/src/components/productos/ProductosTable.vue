<script setup lang="ts">
/**
 * Productos list table (PR10, spec MOD-5).
 *
 * Renders the productos list with the client-joined tipo label, a Sí/No tag
 * for requiere_fabricacion and both money fields es-CO. Editar/Eliminar +
 * the "Variantes" action (lazy nested list) are admin-only via `canEdit`.
 *
 * Presentational: the view owns the API calls, the admin gate and the
 * refresh; this component only emits `edit` / `delete` / `select-variantes`
 * with the clicked row.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c: column sort re-emits the
 * SAME typed event via the parsePrimeVueSort adapter (no header funnels here).
 * Tag/Button cells were migrated in slice 2b.
 */
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import type { ProductoRow } from '@/utils/productos'
import { formatMoney } from '@/utils/format'
import { parsePrimeVueSort } from '@/utils/table-filters'

defineProps<{
  rows: ProductoRow[]
  loading: boolean
  canEdit: boolean
}>()

const emit = defineEmits<{
  edit: [row: ProductoRow]
  delete: [row: ProductoRow]
  'select-variantes': [row: ProductoRow]
  'sort-change': [sort: { prop: string; order: 'asc' | 'desc' | null }]
}>()

/** Normalize DataTable's @sort payload into the typed {prop, order} emit. */
function onDataTableSort(s: { sortField?: string; sortOrder?: number }): void {
  emit('sort-change', parsePrimeVueSort(s))
}
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading" @sort="onDataTableSort">
    <Column field="id" header="#" sortable style="width: 60px" />
    <Column field="tipo" header="Tipo" style="min-width: 120px" />
    <Column field="nombre" header="Nombre" sortable style="min-width: 180px" />
    <Column field="requiere_fabricacion" header="Requiere fabricación" sortable style="width: 160px">
      <template #body="{ data }">
        <Tag :severity="data.requiere_fabricacion ? 'primary' : 'info'">
          {{ data.requiere_fabricacion ? 'Sí' : 'No' }}
        </Tag>
      </template>
    </Column>
    <Column field="precio_venta_sugerido" header="Precio venta sugerido" sortable style="width: 170px" align="right">
      <template #body="{ data }">{{ formatMoney(data.precio_venta_sugerido) }}</template>
    </Column>
    <Column field="costos_operativos_fijos" header="Costos operativos fijos" sortable style="width: 180px" align="right">
      <template #body="{ data }">{{ formatMoney(data.costos_operativos_fijos) }}</template>
    </Column>
    <Column v-if="canEdit" header="Acciones" style="width: 240px">
      <template #body="{ data: row }">
        <Button size="small" severity="secondary" data-test="producto-variantes" @click="$emit('select-variantes', row)">
          Variantes
        </Button>
        <Button size="small" severity="secondary" data-test="edit-producto" @click="$emit('edit', row)">Editar</Button>
        <Button size="small" severity="danger" data-test="delete-producto" @click="$emit('delete', row)">
          Eliminar
        </Button>
      </template>
    </Column>

    <template #empty>
      <div class="producto-empty">Sin productos registrados</div>
    </template>
  </DataTable>
</template>

<style scoped>
.producto-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>
