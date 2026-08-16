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
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c: the insumo header funnel
 * and column sort re-emit the SAME typed events the view consumes, via the
 * parsePrimeVueFilters/parsePrimeVueSort adapters. The funnel only renders
 * when lookups exist (mirroring the old el-table `:filters=[]` behavior).
 */
import { computed, ref } from 'vue'
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
import type { CompraRow } from '@/utils/inventario'

const props = defineProps<{
  rows: CompraRow[]
  loading?: boolean
  /** Insumo options for the header funnel filter (lookup set, design D3). */
  insumos?: { id: number; nombre: string }[]
}>()

const emit = defineEmits<{
  'filter-change': [filters: { insumo_id?: number | null }]
  'sort-change': [sort: { prop: string; order: 'asc' | 'desc' | null }]
}>()

/** Header funnel options for the Insumo column; empty -> no funnel. */
const insumoFilters = computed(() =>
  (props.insumos ?? []).map((i) => ({ text: i.nombre, value: i.id })),
)

/** DataTable lazy filter state (server-side filtering, single constraint per column). */
const filters = ref<Record<string, PrimeVueFilterConstraint>>({
  insumo: { value: null, matchMode: 'equals' },
})

/** Normalize DataTable's @filter payload into the typed single-value emit. */
function onDataTableFilter(e: {
  filters: Record<string, PrimeVueFilterConstraint | PrimeVueFilterConstraint[]>
}): void {
  const normalized = parsePrimeVueFilters(e.filters)
  const insumo_id = parseColumnFilter(normalized.insumo)
  emit('filter-change', {
    insumo_id: typeof insumo_id === 'number' ? insumo_id : null,
  })
}

/** Normalize DataTable's @sort payload into the typed {prop, order} emit. */
function onDataTableSort(s: { sortField?: string; sortOrder?: number }): void {
  emit('sort-change', parsePrimeVueSort(s))
}
</script>

<template>
  <DataTable
    :value="rows"
    lazy
    filterDisplay="menu"
    :loading="loading"
    :filters="filters"
    @filter="onDataTableFilter"
    @sort="onDataTableSort"
  >
    <Column field="id" header="#" sortable style="width: 70px" />
    <Column field="fecha_compra" header="Fecha" sortable style="width: 110px">
      <template #body="{ data }">{{ formatDateTime(data.fecha) }}</template>
    </Column>
    <Column
      field="insumo"
      header="Insumo"
      sortable
      :show-filter-operator="false"
      :show-filter-match-modes="false"
      :show-filter-add-button="false"
      :show-filter-apply-button="false"
      :show-clear-button="false"
      style="min-width: 180px"
    >
      <template v-if="insumoFilters.length > 0" #filter="{ filterModel, filterCallback }">
        <Select
          v-model="filterModel.value"
          :options="insumoFilters"
          optionLabel="text"
          optionValue="value"
          placeholder="Insumo"
          :show-clear="true"
          @change="filterCallback()"
        />
      </template>
    </Column>
    <Column field="cantidad_comprada" header="Cantidad" sortable style="width: 120px" align="right">
      <template #body="{ data }">{{ formatQty(data.cantidad) }}</template>
    </Column>
    <Column field="precio_unitario_compra" header="Precio unitario" sortable style="width: 150px" align="right">
      <template #body="{ data }">{{ formatMoney(data.precio_unitario) }}</template>
    </Column>
    <Column field="costo_total" header="Costo total" style="width: 150px" align="right">
      <template #body="{ data }">{{ formatMoney(data.costo_total) }}</template>
    </Column>

    <template #empty>
      <div class="compra-empty">Sin compras registradas</div>
    </template>
  </DataTable>
</template>

<style scoped>
.compra-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
