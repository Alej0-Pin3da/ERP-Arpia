<script setup lang="ts">
/**
 * Movimientos list table (PR8, spec MOD-3; T9 edit action).
 *
 * Renders the client-side joined rows (buildMovimientoRows output): es-CO
 * formatted fecha/monto, tipo label with a colored tag (Gasto danger,
 * Inversion primary, Retiro warn), the description, the linked socio name
 * (or an em dash), and the settlement key for liquidacion-born rows. The
 * delete action is hidden for read-only roles (can-delete=false); when shown
 * it emits `delete` with the row — the parent owns the confirm dialog, the
 * soft-delete call (expects 200, not 204) and the refresh. The edit action
 * (T9) is shown with can-edit=true and emits `edit` with the row; the parent
 * resolves the full MovimientoRead and opens the prefilled edit form.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1b: the tipo header funnel
 * and column sort re-emit the SAME typed events the view consumes, via the
 * parsePrimeVueFilters/parsePrimeVueSort adapters. Tag/Button cells were
 * migrated in slice 2b.
 */
import { ref } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { formatDateTime, formatMoney } from '@/utils/format'
import {
  parseColumnFilter,
  parsePrimeVueFilters,
  parsePrimeVueSort,
  type PrimeVueFilterConstraint,
} from '@/utils/table-filters'
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

/** DataTable lazy filter state (server-side filtering, single constraint per column). */
const filters = ref<Record<string, PrimeVueFilterConstraint>>({
  tipo: { value: null, matchMode: 'equals' },
})

/** Normalize DataTable's @filter payload into the typed single-value emit. */
function onDataTableFilter(e: {
  filters: Record<string, PrimeVueFilterConstraint | PrimeVueFilterConstraint[]>
}): void {
  const normalized = parsePrimeVueFilters(e.filters)
  const tipo = parseColumnFilter(normalized.tipo)
  emit('filter-change', {
    tipo: (tipo === null ? null : String(tipo)) as MovimientoTipoFilter | null,
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
    <Column field="fecha" header="Fecha" sortable style="width: 110px">
      <template #body="{ data }">{{ formatDateTime(data.fecha) }}</template>
    </Column>
    <Column
      field="tipo"
      header="Tipo"
      sortable
      :show-filter-operator="false"
      :show-filter-match-modes="false"
      :show-filter-add-button="false"
      :show-filter-apply-button="false"
      :show-clear-button="false"
      style="width: 120px"
    >
      <template #body="{ data }">
        <Tag :severity="tipoMovimientoTagType(data.tipo)">{{ tipoMovimientoLabel(data.tipo) }}</Tag>
      </template>
      <template #filter="{ filterModel, filterCallback }">
        <Select
          v-model="filterModel.value"
          :options="tipoFilters"
          optionLabel="text"
          optionValue="value"
          placeholder="Tipo"
          :show-clear="true"
          @change="filterCallback()"
        />
      </template>
    </Column>
    <Column field="descripcion" header="Descripción" sortable style="min-width: 220px" />
    <Column field="socio" header="Socio" sortable style="min-width: 140px" />
    <Column field="monto" header="Monto" sortable style="width: 160px" align="right">
      <template #body="{ data }">{{ formatMoney(data.monto) }}</template>
    </Column>
    <Column header="Liquidación" style="width: 110px">
      <template #body="{ data }">{{ data.liquidacion_id ?? '—' }}</template>
    </Column>
    <Column v-if="canEdit || canDelete" header="Acciones" style="width: 150px" align="center">
      <template #body="{ data: row }">
        <Button
          v-if="canEdit"
          link
          size="small"
          data-test="edit-movimiento"
          @click="emit('edit', row)"
        >
          Editar
        </Button>
        <Button
          v-if="canDelete"
          text
          severity="danger"
          size="small"
          data-test="delete-movimiento"
          @click="emit('delete', row)"
        >
          Eliminar
        </Button>
      </template>
    </Column>

    <template #empty>
      <div class="movimiento-empty">Sin movimientos registrados</div>
    </template>
  </DataTable>
</template>

<style scoped>
.movimiento-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
