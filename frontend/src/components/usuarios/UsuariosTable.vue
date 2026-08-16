<script setup lang="ts">
/**
 * Usuarios list table (PR11, spec MOD-5 usuarios).
 *
 * Admin-only module: id, nombre, email and the rol shown with its es-CO
 * label (Administrador/Operador/Consulta, reusing menu.roleLabel) and a
 * rol-colored tag. Editar emits the row; Eliminar is HIDDEN for the current
 * user's own row ("can't delete self" — the backend additionally rejects
 * DELETE /usuarios/{self} with 400 "Cannot delete your own user"). The view
 * owns the edit form and the API calls.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. el-tag/el-button cells
 * stay until slice 2b.
 */
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import { roleLabel } from '@/utils/menu'
import { rolTagType } from '@/utils/usuarios'
import type { UsuarioRead } from '@/types/api.d'

const props = defineProps<{
  rows: UsuarioRead[]
  loading?: boolean
  /** Current session user id — its own row loses the delete action. */
  currentUserId: number | null
}>()

const emit = defineEmits<{ edit: [row: UsuarioRead]; delete: [row: UsuarioRead] }>()

function isSelf(row: UsuarioRead): boolean {
  return props.currentUserId !== null && row.id === props.currentUserId
}
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading">
    <Column field="id" header="#" style="width: 70px" align="center" />
    <Column field="nombre" header="Nombre" style="min-width: 200px" />
    <Column field="email" header="Email" style="min-width: 220px" />
    <Column field="rol" header="Rol" style="width: 150px" align="center">
      <template #body="{ data }">
        <el-tag :type="rolTagType(data.rol)" size="small">{{ roleLabel(data.rol) }}</el-tag>
      </template>
    </Column>
    <Column header="Acciones" style="width: 150px" align="center">
      <template #body="{ data: row }">
        <el-button link type="primary" size="small" data-test="edit-usuario" @click="emit('edit', row)">
          Editar
        </el-button>
        <el-button
          v-if="!isSelf(row)"
          link
          type="danger"
          size="small"
          data-test="delete-usuario"
          @click="emit('delete', row)"
        >
          Eliminar
        </el-button>
      </template>
    </Column>

    <template #empty>
      <div class="usuario-empty">Sin usuarios registrados</div>
    </template>
  </DataTable>
</template>

<style scoped>
.usuario-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
