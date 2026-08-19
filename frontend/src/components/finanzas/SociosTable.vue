<script setup lang="ts">
/**
 * Socios list table (PR8, spec MOD-3).
 *
 * Renders SociosConfiguracionRead rows with es-CO percentages plus the
 * sum-to-100 progress ("current sum vs 100"): a PrimeVue ProgressBar whose
 * value turns green at exactly 100 (yellow below — the backend enforces an
 * exact-100 sum on create and a never-above-100 rule on update, both 422).
 * Edit/delete actions are hidden for read-only roles (can-edit=false); when
 * shown they emit `edit`/`delete` with the row — the parent owns the PATCH,
 * the DELETE (409 when the socio has payouts) and the refresh.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1b: column sort re-emits the
 * SAME typed event via the parsePrimeVueSort adapter (no header funnels here).
 * The el-progress became a ProgressBar in slice 3a; the Button cells were
 * migrated in slice 2b.
 */
import { computed } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import ProgressBar from 'primevue/progressbar'
import { formatQty } from '@/utils/format'
import { parsePrimeVueSort } from '@/utils/table-filters'
import { sumaParticipacion } from '@/utils/finanzas'
import type { components } from '@/types/api.d'

type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']

const props = defineProps<{
  rows: SocioConfiguracionRead[]
  loading?: boolean
  /** False for consulta (read-only) — hides the edit/delete actions. */
  canEdit?: boolean
}>()

const emit = defineEmits<{
  edit: [row: SocioConfiguracionRead]
  delete: [row: SocioConfiguracionRead]
  'sort-change': [sort: { prop: string; order: 'asc' | 'desc' | null }]
}>()

/** Sum-to-100 progress: current participation vs the 100 target. */
const sum = computed(() => sumaParticipacion(props.rows))

/** Normalize DataTable's @sort payload into the typed {prop, order} emit. */
function onDataTableSort(s: { sortField?: string; sortOrder?: number }): void {
  emit('sort-change', parsePrimeVueSort(s))
}
</script>

<template>
  <div>
    <div v-if="rows.length > 0" class="socios-progress" data-test="socios-progress">
      <span class="socios-progress-label">
        Participación total: {{ formatQty(sum) }}% / 100%
      </span>
      <ProgressBar
        :value="Math.min(Math.round(sum), 100)"
        :showValue="true"
        :class="sum === 100 ? 'socios-progress-bar-success' : 'socios-progress-bar-warning'"
        class="socios-progress-bar"
      />
    </div>

    <DataTable :value="rows" lazy :loading="loading" @sort="onDataTableSort">
      <Column field="id" header="#" sortable style="width: 70px" />
      <Column field="nombre" header="Nombre" sortable style="min-width: 220px" />
      <Column field="porcentaje_participacion" header="Participación" sortable style="width: 160px" align="right">
        <template #body="{ data }">{{ formatQty(data.porcentaje_participacion) }}%</template>
      </Column>
      <Column v-if="canEdit" header="Acciones" style="width: 160px" align="center">
        <template #body="{ data: row }">
          <Button link size="small" data-test="edit-socio" @click="emit('edit', row)">
            Editar
          </Button>
          <Button text severity="danger" size="small" data-test="delete-socio" @click="emit('delete', row)">
            Eliminar
          </Button>
        </template>
      </Column>

      <template #empty>
        <div class="socio-empty">Sin socios configurados</div>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.socios-progress {
  margin-bottom: 1rem;
  max-width: 32rem;
}

.socios-progress-label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  color: var(--arpia-text-regular);
}

.socios-progress-bar {
  width: 100%;
}

.socios-progress-bar-success {
  /* EP status=success parity: green bar at exactly 100. */
  --p-progressbar-value-background: var(--p-green-500);
}

.socios-progress-bar-warning {
  /* EP status=warning parity: yellow bar below 100. */
  --p-progressbar-value-background: var(--p-yellow-500);
}

.socio-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>
