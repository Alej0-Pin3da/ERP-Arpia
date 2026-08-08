<script setup lang="ts">
/**
 * Devoluciones list table (task 2.3, spec MOD-2).
 *
 * Renders the client-side joined rows (buildDevolucionRows output): es-CO
 * formatted fecha/monto, venta_id, tipo label with a colored tag (total
 * danger — cancels the sale; parcial warning), motivo (or an em dash), the
 * items count, and expandable item lines with the product name and the
 * sale-time snapshot subtotal. Missing products degrade to "Producto #{id}".
 */
import { formatDateTime, formatMoney, formatQty } from '@/utils/format'
import { tipoLabel, tipoTagType, type DevolucionRow } from '@/utils/devoluciones'

defineProps<{
  rows: DevolucionRow[]
  loading?: boolean
}>()
</script>

<template>
  <el-table :data="rows" v-loading="loading">
    <el-table-column type="expand">
      <template #default="{ row }">
        <el-table :data="row.items" size="small" class="devolucion-detail-table">
          <el-table-column prop="nombre" label="Producto" min-width="180" />
          <el-table-column label="Cantidad" width="110" align="right">
            <template #default="{ row: item }">{{ formatQty(item.cantidad) }}</template>
          </el-table-column>
          <el-table-column label="Subtotal" width="130" align="right">
            <template #default="{ row: item }">{{ formatMoney(item.subtotal) }}</template>
          </el-table-column>
        </el-table>
      </template>
    </el-table-column>

    <el-table-column prop="id" label="#" width="70" />
    <el-table-column label="Fecha" width="110">
      <template #default="{ row }">{{ formatDateTime(row.fecha) }}</template>
    </el-table-column>
    <el-table-column prop="venta_id" label="Venta" width="90" align="right" />
    <el-table-column label="Tipo" width="110">
      <template #default="{ row }">
        <el-tag :type="tipoTagType(row.tipo)" size="small">{{ tipoLabel(row.tipo) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="motivo" label="Motivo" min-width="220" />
    <el-table-column prop="items.length" label="Items" width="80" align="right" />
    <el-table-column label="Monto reembolsado" width="170" align="right">
      <template #default="{ row }">{{ formatMoney(row.monto_reembolsado) }}</template>
    </el-table-column>

    <template #empty>
      <el-empty description="Sin devoluciones registradas" :image-size="80" />
    </template>
  </el-table>
</template>

<style scoped>
.devolucion-detail-table {
  padding: 0 1rem 0.5rem 3rem;
  background: var(--el-fill-color-lighter);
}
</style>
