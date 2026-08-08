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
 */
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
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="insumo" label="Insumo" min-width="180" />
    <el-table-column prop="unidad_medida" label="Unidad" width="100" />
    <el-table-column label="Cantidad requerida" width="150" align="right">
      <template #default="{ row }">{{ formatQty(row.cantidad_requerida) }}</template>
    </el-table-column>
    <el-table-column label="Desperdicio" width="120" align="right">
      <template #default="{ row }">{{ formatQty(row.porcentaje_desperdicio) }} %</template>
    </el-table-column>
    <el-table-column v-if="canEdit" label="Acciones" width="180" fixed="right">
      <template #default="{ row }">
        <el-button size="small" data-test="edit-bom-insumo" @click="$emit('edit', row)">Editar</el-button>
        <el-button size="small" type="danger" data-test="delete-bom-insumo" @click="$emit('delete', row)">
          Eliminar
        </el-button>
      </template>
    </el-table-column>
    <template #empty>
      <el-empty description="Sin insumos en la receta" />
    </template>
  </el-table>
</template>
