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
 */
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
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="producto" label="Producto incluido" min-width="220" />
    <el-table-column label="Cantidad" width="140" align="right">
      <template #default="{ row }">{{ formatQty(row.cantidad) }}</template>
    </el-table-column>
    <el-table-column v-if="canEdit" label="Acciones" width="180" fixed="right">
      <template #default="{ row }">
        <el-button size="small" data-test="edit-bom-producto" @click="$emit('edit', row)">Editar</el-button>
        <el-button size="small" type="danger" data-test="delete-bom-producto" @click="$emit('delete', row)">
          Eliminar
        </el-button>
      </template>
    </el-table-column>
    <template #empty>
      <el-empty description="Sin productos en el combo" />
    </template>
  </el-table>
</template>
