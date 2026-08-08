<script setup lang="ts">
/**
 * Generic maestros table (PR11, spec MOD-5).
 *
 * One el-table renders every master-data entity from its column config
 * (`columns` from `MAESTRO_ENTITIES`): each configured column shows the row
 * value, and empty/null optionals render an em dash ('—'). The Editar /
 * Eliminar actions are ADMIN ONLY (can-edit=false hides them for
 * operador/consulta — the backend enforces require_admin on every write);
 * when shown they emit `edit`/`delete` with the row — the view owns the
 * forms, the confirm dialog and the API calls. The entity's `emptyText`
 * drives the empty state.
 */
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
</script>

<template>
  <el-table :data="rows" v-loading="loading">
    <el-table-column
      v-for="column in columns"
      :key="column.key"
      :prop="column.key"
      :label="column.label"
      :width="column.width"
      :min-width="column.minWidth"
      :align="column.align"
    >
      <template #default="{ row }">{{ cell(row, column) }}</template>
    </el-table-column>

    <el-table-column v-if="canEdit" label="Acciones" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" data-test="edit-maestro" @click="emit('edit', row)">
          Editar
        </el-button>
        <el-button link type="danger" size="small" data-test="delete-maestro" @click="emit('delete', row)">
          Eliminar
        </el-button>
      </template>
    </el-table-column>

    <template #empty>
      <el-empty :description="emptyText" :image-size="80" />
    </template>
  </el-table>
</template>
