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
 */
import type { ProductoRow } from '@/utils/productos'
import { formatMoney } from '@/utils/format'

defineProps<{
  rows: ProductoRow[]
  loading: boolean
  canEdit: boolean
}>()

defineEmits<{
  edit: [row: ProductoRow]
  delete: [row: ProductoRow]
  'select-variantes': [row: ProductoRow]
}>()
</script>

<template>
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="id" label="#" width="60" />
    <el-table-column prop="tipo" label="Tipo" min-width="120" />
    <el-table-column prop="nombre" label="Nombre" min-width="180" />
    <el-table-column label="Requiere fabricación" width="160">
      <template #default="{ row }">
        <el-tag :type="row.requiere_fabricacion ? 'primary' : 'info'">
          {{ row.requiere_fabricacion ? 'Sí' : 'No' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="Precio venta sugerido" width="170" align="right">
      <template #default="{ row }">{{ formatMoney(row.precio_venta_sugerido) }}</template>
    </el-table-column>
    <el-table-column label="Costos operativos fijos" width="180" align="right">
      <template #default="{ row }">{{ formatMoney(row.costos_operativos_fijos) }}</template>
    </el-table-column>
    <el-table-column v-if="canEdit" label="Acciones" width="240" fixed="right">
      <template #default="{ row }">
        <el-button size="small" data-test="producto-variantes" @click="$emit('select-variantes', row)">
          Variantes
        </el-button>
        <el-button size="small" data-test="edit-producto" @click="$emit('edit', row)">Editar</el-button>
        <el-button size="small" type="danger" data-test="delete-producto" @click="$emit('delete', row)">
          Eliminar
        </el-button>
      </template>
    </el-table-column>
    <template #empty>
      <el-empty description="Sin productos registrados" />
    </template>
  </el-table>
</template>
