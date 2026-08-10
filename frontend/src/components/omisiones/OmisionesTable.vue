<script setup lang="ts">
/**
 * Migracion omisiones table (PR3, spec MIG-3/MIG-4).
 *
 * Presentational: renders corrida/fase/hoja/fila/celda/nivel/mensaje/resuelta
 * rows. The "Marcar resuelta"/"Reabrir" action emits the row and is shown
 * ONLY when the view grants it (admin-only, D9 — the PATCH endpoint is
 * require_admin server-side; the UI is the read-side mirror).
 */
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
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="id" label="#" width="70" align="center" />
    <el-table-column prop="corrida_id" label="Corrida" min-width="200" show-overflow-tooltip />
    <el-table-column prop="fase" label="Fase" width="80" align="center" />
    <el-table-column prop="hoja" label="Hoja" min-width="140" show-overflow-tooltip />
    <el-table-column prop="fila" label="Fila" width="70" align="center" />
    <el-table-column prop="celda" label="Celda" width="90" align="center" />
    <el-table-column label="Nivel" width="100" align="center">
      <template #default="{ row }">
        <el-tag :type="row.nivel === 'ERROR' ? 'danger' : 'warning'" size="small">
          {{ row.nivel }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="mensaje" label="Mensaje" min-width="260" show-overflow-tooltip />
    <el-table-column label="Resuelta" width="110" align="center">
      <template #default="{ row }">
        <el-tag :type="row.resuelta ? 'success' : 'info'" size="small">
          {{ row.resuelta ? 'Sí' : 'No' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column v-if="canResolve" label="Acciones" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" data-test="toggle-omision" @click="emit('toggle', row)">
          {{ row.resuelta ? 'Reabrir' : 'Marcar resuelta' }}
        </el-button>
      </template>
    </el-table-column>

    <template #empty>
      <el-empty description="Sin omisiones registradas" :image-size="80" />
    </template>
  </el-table>
</template>
