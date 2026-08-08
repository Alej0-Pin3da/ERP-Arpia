<script setup lang="ts">
/**
 * Nested variantes table (PR10, spec MOD-5).
 *
 * Lists the variantes of ONE selected product (lazily fetched by the view:
 * GET /productos/{id}/variantes). The backend VarianteProductoRead has NO
 * costo_adicional — only nombre_variante + precio_venta, so those are the
 * two columns; a null precio renders as an em dash. Editar/Eliminar are
 * admin-only via `canEdit`.
 *
 * Presentational: emits `edit` / `delete` with the clicked row.
 */
import type { components } from '@/types/api.d'
import { formatMoney } from '@/utils/format'

type VarianteProductoRead = components['schemas']['VarianteProductoRead']

defineProps<{
  variantes: VarianteProductoRead[]
  loading: boolean
  canEdit: boolean
}>()

defineEmits<{
  edit: [variante: VarianteProductoRead]
  delete: [variante: VarianteProductoRead]
}>()
</script>

<template>
  <el-table :data="variantes" v-loading="loading">
    <el-table-column prop="nombre_variante" label="Variante" min-width="160" />
    <el-table-column label="Precio de venta" min-width="140" align="right">
      <template #default="{ row }">
        {{ row.precio_venta == null || row.precio_venta === '' ? '—' : formatMoney(row.precio_venta) }}
      </template>
    </el-table-column>
    <el-table-column v-if="canEdit" label="Acciones" width="180" fixed="right">
      <template #default="{ row }">
        <el-button size="small" data-test="edit-variante" @click="$emit('edit', row)">Editar</el-button>
        <el-button size="small" type="danger" data-test="delete-variante" @click="$emit('delete', row)">
          Eliminar
        </el-button>
      </template>
    </el-table-column>
    <template #empty>
      <el-empty description="Sin variantes registradas" />
    </template>
  </el-table>
</template>
