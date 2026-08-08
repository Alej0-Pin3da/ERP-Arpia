<script setup lang="ts">
/**
 * Movimientos list table (PR8, spec MOD-3).
 *
 * Renders the client-side joined rows (buildMovimientoRows output): es-CO
 * formatted fecha/monto, tipo label with a colored tag (Gasto danger,
 * Inversion primary, Retiro warning), the description, the linked socio name
 * (or an em dash), and the settlement key for liquidacion-born rows. The
 * delete action is hidden for read-only roles (can-delete=false); when shown
 * it emits `delete` with the row — the parent owns the confirm dialog, the
 * soft-delete call (expects 200, not 204) and the refresh.
 */
import { formatDateTime, formatMoney } from '@/utils/format'
import { tipoMovimientoLabel, tipoMovimientoTagType, type MovimientoRow } from '@/utils/finanzas'

defineProps<{
  rows: MovimientoRow[]
  loading?: boolean
  /** False for consulta (read-only) — hides the delete action. */
  canDelete?: boolean
}>()

const emit = defineEmits<{ delete: [row: MovimientoRow] }>()
</script>

<template>
  <el-table :data="rows" v-loading="loading">
    <el-table-column prop="id" label="#" width="70" />
    <el-table-column label="Fecha" width="110">
      <template #default="{ row }">{{ formatDateTime(row.fecha) }}</template>
    </el-table-column>
    <el-table-column label="Tipo" width="120">
      <template #default="{ row }">
        <el-tag :type="tipoMovimientoTagType(row.tipo)" size="small">{{ tipoMovimientoLabel(row.tipo) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="descripcion" label="Descripción" min-width="220" />
    <el-table-column prop="socio" label="Socio" min-width="140" />
    <el-table-column label="Monto" width="160" align="right">
      <template #default="{ row }">{{ formatMoney(row.monto) }}</template>
    </el-table-column>
    <el-table-column label="Liquidación" width="110">
      <template #default="{ row }">{{ row.liquidacion_id ?? '—' }}</template>
    </el-table-column>
    <el-table-column v-if="canDelete" label="Acciones" width="110" align="center">
      <template #default="{ row }">
        <el-button
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
