<script setup lang="ts">
/**
 * Compras list table (PR9, spec MOD-4).
 *
 * Renders the compra rows from buildCompraRows: es-CO fecha, the insumo name
 * joined client-side (CompraInsumoRead carries only insumo_id; the name comes
 * from GET /insumos with an `Insumo #{id}` fallback), cantidad and
 * precio_unitario as raw Decimal strings formatted es-CO, and the line total
 * computed client-side (`cantidad x precio` — the backend CompraInsumoRead has
 * no costo_total field). The parent owns the register form and the POST.
 */
import { formatDateTime, formatMoney, formatQty } from '@/utils/format'
import type { CompraRow } from '@/utils/inventario'

defineProps<{
  rows: CompraRow[]
  loading?: boolean
}>()
</script>

<template>
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="id" label="#" width="70" />
    <el-table-column label="Fecha" width="110">
      <template #default="{ row }">{{ formatDateTime(row.fecha) }}</template>
    </el-table-column>
    <el-table-column prop="insumo" label="Insumo" min-width="180" />
    <el-table-column label="Cantidad" width="120" align="right">
      <template #default="{ row }">{{ formatQty(row.cantidad) }}</template>
    </el-table-column>
    <el-table-column label="Precio unitario" width="150" align="right">
      <template #default="{ row }">{{ formatMoney(row.precio_unitario) }}</template>
    </el-table-column>
    <el-table-column label="Costo total" width="150" align="right">
      <template #default="{ row }">{{ formatMoney(row.costo_total) }}</template>
    </el-table-column>

    <template #empty>
      <el-empty description="Sin compras registradas" :image-size="80" />
    </template>
  </el-table>
</template>
