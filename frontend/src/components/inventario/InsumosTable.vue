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
import { formatMoney, formatQty } from '@/utils/format'
import { stockSeverity, type StockSeverity } from '@/utils/dashboard'
import type { InsumoRead } from '@/types/api.d'

defineProps<{
  rows: InsumoRead[]
  loading?: boolean
  /** False for operador/consulta — hides the admin Editar/Eliminar actions. */
  canEdit?: boolean
}>()

const emit = defineEmits<{ edit: [row: InsumoRead]; delete: [row: InsumoRead] }>()

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
  <el-table :data="rows" :row-class-name="rowClass" v-loading="loading">
    <el-table-column prop="nombre" label="Insumo" min-width="180" />
    <el-table-column label="Categoría" min-width="140">
      <template #default="{ row }">{{ row.nombre_categoria ?? '—' }}</template>
    </el-table-column>
    <el-table-column prop="unidad_medida" label="Unidad" width="100" />
    <el-table-column label="Stock actual" width="130" align="right">
      <template #default="{ row }">{{ formatQty(row.stock_actual) }}</template>
    </el-table-column>
    <el-table-column label="Stock mínimo" width="130" align="right">
      <template #default="{ row }">{{ formatQty(row.stock_minimo) }}</template>
    </el-table-column>
    <el-table-column label="Costo promedio" width="160" align="right">
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
