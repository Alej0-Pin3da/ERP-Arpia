<script setup lang="ts">
/**
 * Insumos list table (PR9, spec MOD-4).
 *
 * Renders the insumo master list straight from GET /insumos — the category
 * name (`nombre_categoria`) comes JOINED FROM THE SERVER, so no client-side
 * join is needed here; a missing name renders an em dash. Quantities and the
 * average cost render es-CO. Rows below their stock minimum are highlighted
 * with a severity tag (Crítico/Bajo) and a row tint, reusing the dashboard
 * `stockSeverity` (DASH-2 pattern). The Editar/Eliminar actions are admin-only
 * (can-edit=false for operador/consulta — the backend enforces require_admin);
 * when shown they emit `edit`/`delete` with the row — the parent owns the
 * create/edit forms, the confirm dialog and the API calls.
 */
import { computed } from 'vue'
import { formatMoney, formatQty } from '@/utils/format'
import { parseColumnFilter } from '@/utils/table-filters'
import { stockSeverity, type StockSeverity } from '@/utils/dashboard'
import type { InsumoRead } from '@/types/api.d'

const props = defineProps<{
  rows: InsumoRead[]
  loading?: boolean
  /** Categoria options for the header funnel filter (lookup set, design D3). */
  categorias?: { id: number; nombre: string }[]
  /** False for operador/consulta — hides the admin Editar/Eliminar actions. */
  canEdit?: boolean
}>()

const emit = defineEmits<{
  edit: [row: InsumoRead]
  delete: [row: InsumoRead]
  'filter-change': [filters: { categoria_id?: number | null }]
  'sort-change': [sort: { prop: string; order: 'asc' | 'desc' | null }]
}>()

/** Header funnel options for the Categoría column; empty array -> no funnel. */
const categoriaFilters = computed(() =>
  (props.categorias ?? []).map((c) => ({ text: c.nombre, value: c.id })),
)

/** Normalize el-table's filter-change into a typed single-value emit. */
function onColumnFilterChange(elFilters: Record<string, unknown[]>): void {
  const categoria_id = parseColumnFilter(elFilters.categoria)
  emit('filter-change', {
    categoria_id: typeof categoria_id === 'number' ? categoria_id : null,
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

type BelowMin = Exclude<StockSeverity, 'ok'>

const SEVERITY_LABEL: Record<BelowMin, string> = {
  danger: 'Crítico',
  warning: 'Bajo',
}

const SEVERITY_TAG: Record<BelowMin, 'danger' | 'warning'> = {
  danger: 'danger',
  warning: 'warning',
}

function severityOf(row: InsumoRead): StockSeverity {
  return stockSeverity(row.stock_actual, row.stock_minimo)
}

/** el-table row class hook — below-min rows get a severity background tint. */
function rowClass({ row }: { row: InsumoRead }): string {
  return stockSeverity(row.stock_actual, row.stock_minimo)
}
</script>

<template>
  <el-table :data="rows" :row-class-name="rowClass" v-loading="loading" @filter-change="onColumnFilterChange" @sort-change="onSortChange">
    <el-table-column prop="nombre" label="Insumo" column-key="nombre" sortable min-width="180" />
    <el-table-column label="Categoría" column-key="categoria" :filters="categoriaFilters" sortable min-width="140" sort-orders="['ascending', 'descending']">
      <template #default="{ row }">{{ row.nombre_categoria ?? '—' }}</template>
    </el-table-column>
    <el-table-column prop="unidad_medida" label="Unidad" column-key="unidad_medida" sortable width="100" />
    <el-table-column label="Stock actual" column-key="stock_actual" sortable width="130" align="right">
      <template #default="{ row }">{{ formatQty(row.stock_actual) }}</template>
    </el-table-column>
    <el-table-column label="Stock mínimo" column-key="stock_minimo" sortable width="130" align="right">
      <template #default="{ row }">{{ formatQty(row.stock_minimo) }}</template>
    </el-table-column>
    <el-table-column label="Costo promedio" column-key="costo_promedio_actual" sortable width="160" align="right">
      <template #default="{ row }">{{ formatMoney(row.costo_promedio_actual) }}</template>
    </el-table-column>
    <el-table-column label="Estado" width="100" align="center">
      <template #default="{ row }">
        <el-tag v-if="severityOf(row) !== 'ok'" :type="SEVERITY_TAG[severityOf(row) as BelowMin]" size="small">
          {{ SEVERITY_LABEL[severityOf(row) as BelowMin] }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column v-if="canEdit" label="Acciones" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" data-test="edit-insumo" @click="emit('edit', row)">
          Editar
        </el-button>
        <el-button link type="danger" size="small" data-test="delete-insumo" @click="emit('delete', row)">
          Eliminar
        </el-button>
      </template>
    </el-table-column>

    <template #empty>
      <el-empty description="Sin insumos registrados" :image-size="80" />
    </template>
  </el-table>
</template>
