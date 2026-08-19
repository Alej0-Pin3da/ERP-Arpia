<script setup lang="ts">
/**
 * Generic maestros table (PR11, spec MOD-5).
 *
 * One DataTable renders every master-data entity from its column config
 * (`columns` from `MAESTRO_ENTITIES`): each configured column shows the row
 * value, and empty/null optionals render an em dash ('—'). The Editar /
 * Eliminar actions are ADMIN ONLY (can-edit=false hides them for
 * operador/consulta — the backend enforces require_admin on every write);
 * when shown they emit `edit`/`delete` with the row — the view owns the
 * forms, the confirm dialog and the API calls. The entity's `emptyText`
 * drives the empty state.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. Button cells were
 * migrated in slice 2b.
 */
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import type { MaestroColumn, MaestroRow } from '@/utils/maestros'

defineProps<{
  rows: MaestroRow[]
  columns: MaestroColumn[]
  /** Empty-state message from the entity config. */
  emptyText: string
  loading?: boolean
  /** False for operador/consulta — hides the admin Editar/Eliminar actions. */
  canEdit?: boolean
}>()

const emit = defineEmits<{ edit: [row: MaestroRow]; delete: [row: MaestroRow] }>()

/** Row cell: null/undefined/empty optionals render an em dash. */
function cell(row: MaestroRow, column: MaestroColumn): string {
  const value = row[column.key]
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

/** Map the config width/minWidth numbers onto a Column style object. */
function columnStyle(column: MaestroColumn): Record<string, string> {
  const style: Record<string, string> = {}
  if (column.width !== undefined) style.width = `${column.width}px`
  if (column.minWidth !== undefined) style.minWidth = `${column.minWidth}px`
  return style
}
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading">
    <Column
      v-for="column in columns"
      :key="column.key"
      :field="column.key"
      :header="column.label"
      :style="columnStyle(column)"
      :align="column.align"
    >
      <template #body="{ data }">{{ cell(data, column) }}</template>
    </Column>

    <Column v-if="canEdit" header="Acciones" style="width: 150px" align="center">
      <template #body="{ data: row }">
        <Button link size="small" data-test="edit-maestro" @click="emit('edit', row)">
          Editar
        </Button>
        <Button text severity="danger" size="small" data-test="delete-maestro" @click="emit('delete', row)">
          Eliminar
        </Button>
      </template>
    </Column>

    <template #empty>
      <div class="maestro-empty">{{ emptyText }}</div>
    </template>
  </DataTable>
</template>

<style scoped>
.maestro-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>
