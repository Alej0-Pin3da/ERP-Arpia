<script setup lang="ts">
/**
 * Ventas list table (task 2.1, spec MOD-1).
 *
 * Renders the client-side joined rows (buildVentaRows output): es-CO formatted
 * fecha/total, canal + estado labels (estado gets a colored tag), a condensed
 * product summary per row, and expandable detail lines with the full
 * product/variant snapshot. Missing products degrade to "Producto #{id}".
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1a: header funnels and sort
 * re-emit the SAME typed events the view already consumes, via the
 * parsePrimeVueFilters/parsePrimeVueSort adapters. el-tag/el-button cells stay
 * until slice 2b; only the gift tooltip uses the PrimeVue v-tooltip directive.
 */
import { ref } from 'vue'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import { formatDateTime, formatMoney, formatQty } from '@/utils/format'
import {
  parseColumnFilter,
  parsePrimeVueFilters,
  parsePrimeVueSort,
  type PrimeVueFilterConstraint,
} from '@/utils/table-filters'
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

/** DataTable lazy filter state (server-side filtering, single constraint per column). */
const filters = ref<Record<string, PrimeVueFilterConstraint>>({
  canal_venta: { value: null, matchMode: 'equals' },
  estado: { value: null, matchMode: 'equals' },
})

/** Expanded rows keyed by row id (nested detail table). */
const expandedRows = ref<Record<string, boolean>>({})

/** Normalize DataTable's @filter payload into the typed single-value emit. */
function onDataTableFilter(e: {
  filters: Record<string, PrimeVueFilterConstraint | PrimeVueFilterConstraint[]>
}): void {
  const normalized = parsePrimeVueFilters(e.filters)
  const canal_venta = parseColumnFilter(normalized.canal_venta)
  const estado = parseColumnFilter(normalized.estado)
  emit('filter-change', {
    canal_venta: canal_venta === null ? null : String(canal_venta),
    estado: estado === null ? null : String(estado),
  })
}

/** Normalize DataTable's @sort payload into the typed {prop, order} emit. */
function onDataTableSort(s: { sortField?: string; sortOrder?: number }): void {
  emit('sort-change', parsePrimeVueSort(s))
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
  <DataTable
    :value="rows"
    v-model:expandedRows="expandedRows"
    dataKey="id"
    lazy
    filterDisplay="menu"
    :loading="loading"
    :filters="filters"
    @filter="onDataTableFilter"
    @sort="onDataTableSort"
  >
    <Column expander style="width: 3rem" />
    <template #expansion="{ data }">
      <DataTable :value="data.detalles" size="small" class="venta-detail-table">
        <Column field="nombre" header="Producto" style="min-width: 180px" />
        <Column field="variante" header="Variante" style="min-width: 120px" />
        <Column header="Cantidad" style="width: 110px" align="right">
          <template #body="{ data: d }">{{ formatQty(d.cantidad) }}</template>
        </Column>
        <Column header="P. unitario" style="width: 130px" align="right">
          <template #body="{ data: d }">{{ formatMoney(d.precio_unitario_aplicado) }}</template>
        </Column>
      </DataTable>
    </template>

    <Column field="id" header="#" sortable style="width: 70px" />
    <Column field="fecha" header="Fecha" sortable style="width: 110px">
      <template #body="{ data }">{{ formatDateTime(data.fecha) }}</template>
    </Column>
    <Column
      field="canal_venta"
      header="Canal"
      sortable
      :show-filter-operator="false"
      :show-filter-match-modes="false"
      :show-filter-add-button="false"
      :show-filter-apply-button="false"
      :show-clear-button="false"
      style="width: 110px"
    >
      <template #body="{ data }">{{ canalLabel(data.canal_venta) }}</template>
      <template #filter="{ filterModel, filterCallback }">
        <Select
          v-model="filterModel.value"
          :options="canalFilters"
          optionLabel="text"
          optionValue="value"
          placeholder="Canal"
          :show-clear="true"
          @change="filterCallback()"
        />
      </template>
    </Column>
    <Column
      field="estado"
      header="Estado"
      sortable
      :show-filter-operator="false"
      :show-filter-match-modes="false"
      :show-filter-add-button="false"
      :show-filter-apply-button="false"
      :show-clear-button="false"
      style="width: 150px"
    >
      <template #body="{ data }">
        <div class="venta-estado-cell">
          <el-tag :type="estadoTagType(data.estado)" size="small">{{ estadoLabel(data.estado) }}</el-tag>
          <el-tag v-if="data.es_regalo" type="warning" size="small" data-test="tag-regalo">Regalo</el-tag>
        </div>
      </template>
      <template #filter="{ filterModel, filterCallback }">
        <Select
          v-model="filterModel.value"
          :options="estadoFilters"
          optionLabel="text"
          optionValue="value"
          placeholder="Estado"
          :show-clear="true"
          @change="filterCallback()"
        />
      </template>
    </Column>
    <Column field="nombre" header="Productos" style="min-width: 220px">
      <template #body="{ data }">{{ productSummary(data) }}</template>
    </Column>
    <Column field="cliente" header="Cliente" sortable style="min-width: 150px" />
    <Column field="detalle_count" header="Detalles" style="width: 90px" align="right" />
    <Column field="total_venta" header="Total" sortable style="width: 130px" align="right">
      <template #body="{ data }">
        <span :class="{ 'total-regalo': data.es_regalo }">
          {{ formatMoney(data.es_regalo ? 0 : data.total_venta) }}
        </span>
      </template>
    </Column>
    <Column v-if="canMarkRegalo" header="Acciones" style="width: 210px" align="center">
      <template #body="{ data: row }">
        <el-button
          v-if="!row.es_regalo"
          v-tooltip="{ value: 'Marcar como regalo', position: 'top' }"
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
    </Column>

    <template #empty>
      <div class="venta-empty">Sin ventas registradas</div>
    </template>
  </DataTable>
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

.venta-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>