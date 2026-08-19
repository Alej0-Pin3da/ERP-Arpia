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
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1b: the categoria header
 * funnel and column sort re-emit the SAME typed events the view consumes, via
 * the parsePrimeVueFilters/parsePrimeVueSort adapters. The funnel only renders
 * when categorias exist (mirroring the old el-table `:filters=[]` behavior).
 * el-tag/el-button cells stay until slice 2b.
 */
import { computed, ref } from 'vue'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import { formatMoney, formatQty } from '@/utils/format'
import {
  parseColumnFilter,
  parsePrimeVueFilters,
  parsePrimeVueSort,
  type PrimeVueFilterConstraint,
} from '@/utils/table-filters'
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

/** DataTable lazy filter state (server-side filtering, single constraint per column). */
const filters = ref<Record<string, PrimeVueFilterConstraint>>({
  categoria: { value: null, matchMode: 'equals' },
})

/** Normalize DataTable's @filter payload into the typed single-value emit. */
function onDataTableFilter(e: {
  filters: Record<string, PrimeVueFilterConstraint | PrimeVueFilterConstraint[]>
}): void {
  const normalized = parsePrimeVueFilters(e.filters)
  const categoria_id = parseColumnFilter(normalized.categoria)
  emit('filter-change', {
    categoria_id: typeof categoria_id === 'number' ? categoria_id : null,
  })
}

/** Normalize DataTable's @sort payload into the typed {prop, order} emit. */
function onDataTableSort(s: { sortField?: string; sortOrder?: number }): void {
  emit('sort-change', parsePrimeVueSort(s))
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

/** DataTable row class hook — below-min rows get a severity background tint. */
function rowClass(row: InsumoRead): string {
  return stockSeverity(row.stock_actual, row.stock_minimo)
}
</script>

<template>
  <DataTable
    :value="rows"
    lazy
    filterDisplay="menu"
    :loading="loading"
    :filters="filters"
    :row-class="rowClass"
    @filter="onDataTableFilter"
    @sort="onDataTableSort"
  >
    <Column field="nombre" header="Insumo" sortable style="min-width: 180px" />
    <Column
      field="categoria"
      header="Categoría"
      sortable
      :show-filter-operator="false"
      :show-filter-match-modes="false"
      :show-filter-add-button="false"
      :show-filter-apply-button="false"
      :show-clear-button="false"
      style="min-width: 140px"
    >
      <template #body="{ data }">{{ data.nombre_categoria ?? '—' }}</template>
      <template v-if="categoriaFilters.length > 0" #filter="{ filterModel, filterCallback }">
        <Select
          v-model="filterModel.value"
          :options="categoriaFilters"
          optionLabel="text"
          optionValue="value"
          placeholder="Categoría"
          :show-clear="true"
          @change="filterCallback()"
        />
      </template>
    </Column>
    <Column field="unidad_medida" header="Unidad" sortable style="width: 100px" />
    <Column field="stock_actual" header="Stock actual" sortable style="width: 130px" align="right">
      <template #body="{ data }">{{ formatQty(data.stock_actual) }}</template>
    </Column>
    <Column field="stock_minimo" header="Stock mínimo" sortable style="width: 130px" align="right">
      <template #body="{ data }">{{ formatQty(data.stock_minimo) }}</template>
    </Column>
    <Column field="costo_promedio_actual" header="Costo promedio" sortable style="width: 160px" align="right">
      <template #body="{ data }">{{ formatMoney(data.costo_promedio_actual) }}</template>
    </Column>
    <Column header="Estado" style="width: 100px" align="center">
      <template #body="{ data }">
        <el-tag v-if="severityOf(data) !== 'ok'" :type="SEVERITY_TAG[severityOf(data) as BelowMin]" size="small">
          {{ SEVERITY_LABEL[severityOf(data) as BelowMin] }}
        </el-tag>
      </template>
    </Column>
    <Column v-if="canEdit" header="Acciones" style="width: 150px" align="center">
      <template #body="{ data: row }">
        <el-button link type="primary" size="small" data-test="edit-insumo" @click="emit('edit', row)">
          Editar
        </el-button>
        <el-button link type="danger" size="small" data-test="delete-insumo" @click="emit('delete', row)">
          Eliminar
        </el-button>
      </template>
    </Column>

    <template #empty>
      <div class="insumo-empty">Sin insumos registrados</div>
    </template>
  </DataTable>
</template>

<style scoped>
.insumo-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
