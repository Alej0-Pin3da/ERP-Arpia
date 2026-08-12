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
import { parseColumnFilter } from '@/utils/table-filters'
import {
  CANAL_VENTAS,
  canalLabel,
  estadoLabel,
  type VentaRow,
} from '@/utils/ventas'

defineProps<{
  rows: VentaRow[]
  loading?: boolean
  /** Show the per-row "Marcar como regalo" action (admin/operador only). */
  canMarkRegalo?: boolean
}>()

const emit = defineEmits<{
  'filter-change': [filters: { canal_venta?: string | null; estado?: string | null }]
  'sort-change': [sort: { prop: string; order: 'asc' | 'desc' | null }]
  'marcar-regalo': [ventaId: number]
  'editar': [row: VentaRow]
  'anular': [ventaId: number]
}>()

/** Header funnel options per column: labels via canalLabel/estadoLabel. */
const canalFilters = CANAL_VENTAS.map((c) => ({ text: canalLabel(c), value: c }))
const estadoFilters = (['completada', 'anulada'] as const).map((e) => ({
  text: estadoLabel(e),
  value: e,
}))

/** Normalize el-table's filter-change into a typed single-value emit. */
function onColumnFilterChange(elFilters: Record<string, unknown[]>): void {
  const canal_venta = parseColumnFilter(elFilters.canal_venta)
  const estado = parseColumnFilter(elFilters.estado)
  emit('filter-change', {
    canal_venta: canal_venta === null ? null : String(canal_venta),
    estado: estado === null ? null : String(estado),
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
  <el-table :data="rows" v-loading="loading" @filter-change="onColumnFilterChange" @sort-change="onSortChange">
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

    <el-table-column prop="id" label="#" column-key="id" sortable width="70" />
    <el-table-column label="Fecha" column-key="fecha" sortable width="110">
      <template #default="{ row }">{{ formatDateTime(row.fecha) }}</template>
    </el-table-column>
    <el-table-column label="Canal" column-key="canal_venta" :filters="canalFilters" sortable width="110">
      <template #default="{ row }">{{ canalLabel(row.canal_venta) }}</template>
    </el-table-column>
    <el-table-column label="Estado" column-key="estado" :filters="estadoFilters" sortable width="150">
      <template #default="{ row }">
        <div class="venta-estado-cell">
          <el-tag :type="estadoTagType(row.estado)" size="small">{{ estadoLabel(row.estado) }}</el-tag>
          <el-tag v-if="row.es_regalo" type="warning" size="small" data-test="tag-regalo">Regalo</el-tag>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="Productos" min-width="220">
      <template #default="{ row }">{{ productSummary(row) }}</template>
    </el-table-column>
    <el-table-column prop="cliente" label="Cliente" column-key="cliente" sortable min-width="150" />
    <el-table-column prop="detalle_count" label="Detalles" width="90" align="right" />
    <el-table-column label="Total" column-key="total_venta" sortable width="130" align="right">
      <template #default="{ row }">
        <span :class="{ 'total-regalo': row.es_regalo }">
          {{ formatMoney(row.es_regalo ? 0 : row.total_venta) }}
        </span>
      </template>
    </el-table-column>
    <el-table-column v-if="canMarkRegalo" label="Acciones" width="210" align="center">
      <template #default="{ row }">
        <el-tooltip
          v-if="!row.es_regalo"
          content="Marcar como regalo"
          placement="top"
        >
          <el-button
            size="small"
            circle
            plain
            type="warning"
            aria-label="Marcar como regalo"
            data-test="marcar-regalo"
            @click="emit('marcar-regalo', row.id)"
          >
            🎁
          </el-button>
        </el-tooltip>
        <el-button
          v-if="row.estado !== 'anulada'"
          link
          type="primary"
          size="small"
          data-test="editar-venta"
          @click="emit('editar', row)"
        >
          Editar
        </el-button>
        <el-button
          v-if="!row.es_regalo && row.estado !== 'anulada'"
          link
          type="danger"
          size="small"
          data-test="anular-venta"
          @click="emit('anular', row.id)"
        >
          Anular
        </el-button>
      </template>
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

.venta-estado-cell {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.total-regalo {
  color: var(--el-text-color-secondary);
  font-style: italic;
}
</style>
