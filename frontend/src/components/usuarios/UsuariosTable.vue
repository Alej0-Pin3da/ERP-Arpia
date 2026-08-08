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
 */
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
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="id" label="#" width="70" align="center" />
    <el-table-column prop="nombre" label="Nombre" min-width="200" />
    <el-table-column prop="email" label="Email" min-width="220" />
    <el-table-column label="Rol" width="150" align="center">
      <template #default="{ row }">
        <el-tag :type="rolTagType(row.rol)" size="small">{{ roleLabel(row.rol) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="Acciones" width="150" align="center">
      <template #default="{ row }">
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
    </el-table-column>

    <template #empty>
      <el-empty description="Sin usuarios registrados" :image-size="80" />
    </template>
  </el-table>
</template>
