<script setup lang="ts">
/**
 * Ventas list table (task 2.1, spec MOD-1).
 *
 * Renders the client-side joined rows (buildVentaRows output): es-CO formatted
 * fecha/total, canal + estado labels (estado gets a colored tag), a condensed
 * product summary per row, and expandable detail lines with the full
 * product/variant snapshot. Missing products degrade to "Producto #{id}".
 */
import { formatDateTime, formatMoney, formatQty } from '@/utils/format'
import { canalLabel, estadoLabel, type VentaRow } from '@/utils/ventas'

defineProps<{
  rows: VentaRow[]
  loading?: boolean
}>()

/** el-tag type per estado: completada success, anulada danger, rest info. */
function estadoTagType(estado: string): 'success' | 'danger' | 'info' {
  if (estado === 'completada') return 'success'
  if (estado === 'anulada') return 'danger'
  return 'info'
}

/** Condensed product summary for the main row: 'Arepa de huevo ×2, ...'. */
function productSummary(row: VentaRow): string {
  return row.detalles.map((d) => `${d.nombre} ×${formatQty(d.cantidad)}`).join(', ')
}
</script>

<template>
  <el-table :data="rows" v-loading="loading">
    <el-table-column type="expand">
      <template #default="{ row }">
        <el-table :data="row.detalles" size="small" class="venta-detail-table">
          <el-table-column prop="nombre" label="Producto" min-width="180" />
          <el-table-column prop="variante" label="Variante" min-width="120" />
          <el-table-column label="Cantidad" width="110" align="right">
            <template #default="{ row: d }">{{ formatQty(d.cantidad) }}</template>
          </el-table-column>
          <el-table-column label="P. unitario" width="130" align="right">
            <template #default="{ row: d }">{{ formatMoney(d.precio_unitario_aplicado) }}</template>
          </el-table-column>
        </el-table>
      </template>
    </el-table-column>

    <el-table-column prop="id" label="#" width="70" />
    <el-table-column label="Fecha" width="110">
      <template #default="{ row }">{{ formatDateTime(row.fecha) }}</template>
    </el-table-column>
    <el-table-column label="Canal" width="110">
      <template #default="{ row }">{{ canalLabel(row.canal_venta) }}</template>
    </el-table-column>
    <el-table-column label="Estado" width="120">
      <template #default="{ row }">
        <el-tag :type="estadoTagType(row.estado)" size="small">{{ estadoLabel(row.estado) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="Productos" min-width="220">
      <template #default="{ row }">{{ productSummary(row) }}</template>
    </el-table-column>
    <el-table-column prop="cliente" label="Cliente" min-width="150" />
    <el-table-column prop="detalle_count" label="Detalles" width="90" align="right" />
    <el-table-column label="Total" width="130" align="right">
      <template #default="{ row }">{{ formatMoney(row.total_venta) }}</template>
    </el-table-column>

    <template #empty>
      <el-empty description="Sin ventas registradas" :image-size="80" />
    </template>
  </el-table>
</template>

<style scoped>
.venta-detail-table {
  padding: 0 1rem 0.5rem 3rem;
  background: var(--el-fill-color-lighter);
}
</style>
