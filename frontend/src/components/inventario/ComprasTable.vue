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
import { computed } from 'vue'
import { formatDateTime, formatMoney, formatQty } from '@/utils/format'
import { parseColumnFilter } from '@/utils/table-filters'
import type { CompraRow } from '@/utils/inventario'

const props = defineProps<{
  rows: CompraRow[]
  loading?: boolean
  /** Insumo options for the header funnel filter (lookup set, design D3). */
  insumos?: { id: number; nombre: string }[]
  /** Proveedor options for the header funnel filter (lookup set, design D3). */
  proveedores?: { id: number; nombre: string }[]
}>()

const emit = defineEmits<{
  'filter-change': [filters: { insumo_id?: number | null; proveedor_id?: number | null }]
  'sort-change': [sort: { prop: string; order: 'asc' | 'desc' | null }]
}>()

/** Header funnel options for the Insumo/Proveedor columns; empty -> no funnel. */
const insumoFilters = computed(() =>
  (props.insumos ?? []).map((i) => ({ text: i.nombre, value: i.id })),
)
const proveedorFilters = computed(() =>
  (props.proveedores ?? []).map((p) => ({ text: p.nombre, value: p.id })),
)

/** Normalize el-table's filter-change into a typed single-value emit. */
function onColumnFilterChange(elFilters: Record<string, unknown[]>): void {
  const insumo_id = parseColumnFilter(elFilters.insumo)
  const proveedor_id = parseColumnFilter(elFilters.proveedor)
  emit('filter-change', {
    insumo_id: typeof insumo_id === 'number' ? insumo_id : null,
    proveedor_id: typeof proveedor_id === 'number' ? proveedor_id : null,
  })
}

/** Normalize el-table's sort-change into a typed {prop, order} emit. */
function onSortChange(s: {
  column: { key?: string; property?: string }
  prop: string
  order: 'ascending' | 'descending' | null
}): void {
  const prop = s.column.key ?? s.column.property ?? s.prop
  emit('sort-change', {
    prop,
    order: s.order === 'ascending' ? 'asc' : s.order === 'descending' ? 'desc' : null,
  })
}
</script>

<template>
  <el-table :data="rows" v-loading="loading" @filter-change="onColumnFilterChange" @sort-change="onSortChange">
    <el-table-column prop="id" label="#" column-key="id" sortable width="70" />
    <el-table-column label="Fecha" column-key="fecha_compra" sortable width="110">
      <template #default="{ row }">{{ formatDateTime(row.fecha) }}</template>
    </el-table-column>
    <el-table-column prop="insumo" label="Insumo" column-key="insumo" :filters="insumoFilters" sortable min-width="180" />
    <el-table-column prop="proveedor" label="Proveedor" column-key="proveedor" :filters="proveedorFilters" sortable min-width="140" />
    <el-table-column label="Cantidad" column-key="cantidad_comprada" sortable width="120" align="right">
      <template #default="{ row }">{{ formatQty(row.cantidad) }}</template>
    </el-table-column>
    <el-table-column label="Precio unitario" column-key="precio_unitario_compra" sortable width="150" align="right">
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
