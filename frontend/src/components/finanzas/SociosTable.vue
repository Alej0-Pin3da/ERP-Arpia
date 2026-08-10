<script setup lang="ts">
/**
 * Socios list table (PR8, spec MOD-3).
 *
 * Renders SociosConfiguracionRead rows with es-CO percentages plus the
 * sum-to-100 progress ("current sum vs 100"): an el-progress whose status
 * turns success at exactly 100 (warning below — the backend enforces an
 * exact-100 sum on create and a never-above-100 rule on update, both 422).
 * Edit/delete actions are hidden for read-only roles (can-edit=false); when
 * shown they emit `edit`/`delete` with the row — the parent owns the PATCH,
 * the DELETE (409 when the socio has payouts) and the refresh.
 */
import { computed } from 'vue'

import { formatQty } from '@/utils/format'
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
  <div>
    <div v-if="rows.length > 0" class="socios-progress" data-test="socios-progress">
      <span class="socios-progress-label">
        Participación total: {{ formatQty(sum) }}% / 100%
      </span>
      <el-progress
        :percentage="Math.min(Math.round(sum), 100)"
        :status="sum === 100 ? 'success' : 'warning'"
        :stroke-width="10"
        class="socios-progress-bar"
      />
    </div>

    <el-table :data="rows" v-loading="loading" @sort-change="onSortChange">
      <el-table-column prop="id" label="#" column-key="id" sortable width="70" />
      <el-table-column prop="nombre" label="Nombre" column-key="nombre" sortable min-width="220" />
      <el-table-column label="Participación" column-key="porcentaje_participacion" sortable width="160" align="right">
        <template #default="{ row }">{{ formatQty(row.porcentaje_participacion) }}%</template>
      </el-table-column>
      <el-table-column v-if="canEdit" label="Acciones" width="160" align="center">
        <template #default="{ row }">
          <el-button link type="primary" size="small" data-test="edit-socio" @click="emit('edit', row)">
            Editar
          </el-button>
          <el-button link type="danger" size="small" data-test="delete-socio" @click="emit('delete', row)">
            Eliminar
          </el-button>
        </template>
      </el-table-column>

      <template #empty>
        <el-empty description="Sin socios configurados" :image-size="80" />
      </template>
    </el-table>
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
  color: var(--el-text-color-regular);
}

.socios-progress-bar {
  width: 100%;
}
</style>
