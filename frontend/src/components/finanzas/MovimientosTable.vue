<script setup lang="ts">
/**
 * Movimientos list table (PR8, spec MOD-3; T9 edit action).
 *
 * Renders the client-side joined rows (buildMovimientoRows output): es-CO
 * formatted fecha/monto, tipo label with a colored tag (Gasto danger,
 * Inversion primary, Retiro warning), the description, the linked socio name
 * (or an em dash), and the settlement key for liquidacion-born rows. The
 * delete action is hidden for read-only roles (can-delete=false); when shown
 * it emits `delete` with the row — the parent owns the confirm dialog, the
 * soft-delete call (expects 200, not 204) and the refresh. The edit action
 * (T9) is shown with can-edit=true and emits `edit` with the row; the parent
 * resolves the full MovimientoRead and opens the prefilled edit form.
 */
import { formatDateTime, formatMoney } from '@/utils/format'
import { parseColumnFilter } from '@/utils/table-filters'
import {
  TIPO_MOVIMIENTO,
  tipoMovimientoLabel,
  tipoMovimientoTagType,
  type MovimientoRow,
} from '@/utils/finanzas'

defineProps<{
  rows: MovimientoRow[]
  loading?: boolean
  /** False for consulta (read-only) — hides the delete action. */
  canDelete?: boolean
  /** False for consulta (read-only) — hides the edit action (T9). */
  canEdit?: boolean
}>()

type MovimientoTipoFilter = 'Gasto' | 'Inversion' | 'Retiro'

const emit = defineEmits<{
  delete: [row: MovimientoRow]
  edit: [row: MovimientoRow]
  'filter-change': [filters: { tipo?: MovimientoTipoFilter | null }]
  'sort-change': [sort: { prop: string; order: 'asc' | 'desc' | null }]
}>()

/** Header funnel options for the Tipo column (labels via tipoMovimientoLabel). */
const tipoFilters = TIPO_MOVIMIENTO.map((t) => ({ text: tipoMovimientoLabel(t), value: t }))

/** Normalize el-table's filter-change into a typed single-value emit. */
function onColumnFilterChange(elFilters: Record<string, unknown[]>): void {
  const tipo = parseColumnFilter(elFilters.tipo)
  emit('filter-change', {
    tipo: (tipo === null ? null : String(tipo)) as MovimientoTipoFilter | null,
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
    <el-table-column label="Fecha" column-key="fecha" sortable width="110">
      <template #default="{ row }">{{ formatDateTime(row.fecha) }}</template>
    </el-table-column>
    <el-table-column label="Tipo" column-key="tipo" :filters="tipoFilters" sortable width="120">
      <template #default="{ row }">
        <el-tag :type="tipoMovimientoTagType(row.tipo)" size="small">{{ tipoMovimientoLabel(row.tipo) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="descripcion" label="Descripción" column-key="descripcion" sortable min-width="220" />
    <el-table-column prop="socio" label="Socio" column-key="socio" sortable min-width="140" />
    <el-table-column label="Monto" column-key="monto" sortable width="160" align="right">
      <template #default="{ row }">{{ formatMoney(row.monto) }}</template>
    </el-table-column>
    <el-table-column label="Liquidación" width="110">
      <template #default="{ row }">{{ row.liquidacion_id ?? '—' }}</template>
    </el-table-column>
    <el-table-column v-if="canEdit || canDelete" label="Acciones" width="150" align="center">
      <template #default="{ row }">
        <el-button
          v-if="canEdit"
          link
          type="primary"
          size="small"
          data-test="edit-movimiento"
          @click="emit('edit', row)"
        >
          Editar
        </el-button>
        <el-button
          v-if="canDelete"
          link
          type="danger"
          size="small"
          data-test="delete-movimiento"
          @click="emit('delete', row)"
        >
          Eliminar
        </el-button>
      </template>
    </el-table-column>

    <template #empty>
      <el-empty description="Sin movimientos registrados" :image-size="80" />
    </template>
  </el-table>
</template>
