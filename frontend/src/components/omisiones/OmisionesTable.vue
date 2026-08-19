<script setup lang="ts">
/**
 * Migracion omisiones table (PR3, spec MIG-3/MIG-4).
 *
 * Presentational: renders corrida/fase/hoja/fila/celda/nivel/mensaje/resuelta
 * rows. The "Marcar resuelta"/"Reabrir" action emits the row and is shown
 * ONLY when the view grants it (admin-only, D9 — the PATCH endpoint is
 * require_admin server-side; the UI is the read-side mirror).
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. el-tag/el-button cells
 * stay until slice 2b.
 */
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import type { OmisionRead } from '@/types/api.d'

defineProps<{
  rows: OmisionRead[]
  loading?: boolean
  /** Admin-only: render the marcar-resuelta action column (D9). */
  canResolve?: boolean
}>()

const emit = defineEmits<{ toggle: [row: OmisionRead] }>()
</script>

<template>
  <DataTable :value="rows" lazy :loading="loading">
    <Column field="id" header="#" style="width: 70px" align="center" />
    <Column field="corrida_id" header="Corrida" style="min-width: 200px" />
    <Column field="fase" header="Fase" style="width: 80px" align="center" />
    <Column field="hoja" header="Hoja" style="min-width: 140px" />
    <Column field="fila" header="Fila" style="width: 70px" align="center" />
    <Column field="celda" header="Celda" style="width: 90px" align="center" />
    <Column header="Nivel" style="width: 100px" align="center">
      <template #body="{ data }">
        <el-tag :type="data.nivel === 'ERROR' ? 'danger' : 'warning'" size="small">
          {{ data.nivel }}
        </el-tag>
      </template>
    </Column>
    <Column field="mensaje" header="Mensaje" style="min-width: 260px" />
    <Column header="Resuelta" style="width: 110px" align="center">
      <template #body="{ data }">
        <el-tag :type="data.resuelta ? 'success' : 'info'" size="small">
          {{ data.resuelta ? 'Sí' : 'No' }}
        </el-tag>
      </template>
    </Column>
    <Column v-if="canResolve" header="Acciones" style="width: 150px" align="center">
      <template #body="{ data: row }">
        <el-button link type="primary" size="small" data-test="toggle-omision" @click="emit('toggle', row)">
          {{ row.resuelta ? 'Reabrir' : 'Marcar resuelta' }}
        </el-button>
      </template>
    </Column>

    <template #empty>
      <div class="omision-empty">Sin omisiones registradas</div>
    </template>
  </DataTable>
</template>

<style scoped>
.omision-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
</style>
