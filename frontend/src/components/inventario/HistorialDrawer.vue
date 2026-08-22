<script setup lang="ts">
/**
 * HistorialDrawer (PR2 — REQ-CI-003 SCN-CI-005).
 *
 * PrimeVue Drawer: date/qty/prev→new stock/cost/total/factura + CSV export
 * calling buildHistorialCsv. Display-only; backend remains authoritative.
 */
import { computed } from 'vue'
import Button from 'primevue/button'
import Drawer from 'primevue/drawer'
import { buildHistorialCsv, type HistorialCsvRow, CSV_HEADER } from '@/utils/inventario'
import { formatDate, formatMoney, formatQty, parseDecimal } from '@/utils/format'
import type { CompraInsumoRead, InsumoRead } from '@/types/api.d'

const props = defineProps<{
  visible: boolean
  insumo?: InsumoRead | null
  compras: CompraInsumoRead[]
  loading?: boolean
}>()

const emit = defineEmits<{ 'update:visible': [v: boolean] }>()

function onUpdateVisible(v: boolean): void {
  emit('update:visible', v)
}

/**
 * Compute prev→new rows from chronological history (ASC) starting at
 * synthetic zero-stock when initial snapshot is unknown. This is display-only
 * — backend WAC is authoritative — but yields the SCN-CI-005 parity case
 * 10@5+10@9 → prev 10@5 → new 20@7.0000 when history starts empty.
 */
const historialRows = computed<HistorialCsvRow[]>(() => {
  const sorted = [...props.compras].sort(
    (a, b) => new Date(a.fecha_compra).getTime() - new Date(b.fecha_compra).getTime(),
  )
  let runStock = 0
  let runCost = 0
  const rows: HistorialCsvRow[] = []
  for (const c of sorted) {
    const qty = parseDecimal(c.cantidad_comprada) ?? 0
    const unit = parseDecimal(c.precio_unitario_compra) ?? 0
    const total = qty * unit
    const prevStock = runStock
    const prevCost = runCost
    const newStock = prevStock + qty
    const newCost = newStock > 0 ? (prevStock * prevCost + qty * unit) / newStock : unit
    rows.push({
      fecha: formatDate(c.fecha_compra) ?? c.fecha_compra,
      cantidad: c.cantidad_comprada,
      prevStock: prevStock.toFixed(2),
      newStock: newStock.toFixed(2),
      prevCost: prevCost.toFixed(4),
      newCost: newCost.toFixed(4),
      total: total.toFixed(2),
      factura: (c as unknown as { factura?: string | null }).factura ?? '',
    })
    runStock = newStock
    runCost = newStock > 0 ? newCost : runCost
  }
  // Drawer expects newest first (SCN-CI-005) — reverse for display/CSV consistency.
  return rows.reverse()
})

function downloadCsv(): void {
  const csv = buildHistorialCsv(historialRows.value)
  // Guard for test env without Blob URL support — still validate header.
  if (typeof document === 'undefined') return
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `historial-${props.insumo?.nombre ?? 'insumo'}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// Exposed for tests: header constant parity.
defineExpose({ CSV_HEADER })
</script>

<template>
  <Drawer :visible="visible" position="right" :style="{ width: '42rem', maxWidth: '95vw' }" header="Historial de compras" @update:visible="onUpdateVisible">
    <div v-if="loading" class="drawer-loading">Cargando…</div>
    <template v-else>
      <div v-if="insumo" class="drawer-insumo">
        <strong>{{ insumo.nombre }}</strong>
        <span class="drawer-meta">Stock {{ formatQty(insumo.stock_actual) }} · {{ formatMoney(insumo.costo_promedio_actual) }}</span>
      </div>

      <div v-if="historialRows.length === 0" class="drawer-empty">Sin compras registradas.</div>

      <div v-else class="drawer-table-wrap">
        <table class="drawer-table" data-test="historial-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Cantidad</th>
              <th>Stock (prev → new)</th>
              <th>Costo (prev → new)</th>
              <th>Total</th>
              <th>Factura</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in historialRows" :key="i" data-test="historial-row">
              <td>{{ r.fecha }}</td>
              <td>{{ r.cantidad }}</td>
              <td>{{ r.prevStock }} → {{ r.newStock }}</td>
              <td>{{ r.prevCost }} → {{ r.newCost }}</td>
              <td>{{ r.total }}</td>
              <td>{{ r.factura || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="drawer-actions">
        <Button label="Exportar CSV" icon="pi pi-download" severity="secondary" :disabled="historialRows.length === 0" data-test="export-csv" @click="downloadCsv" />
      </div>
    </template>
  </Drawer>
</template>

<style scoped>
.drawer-insumo {
  display: flex;
  flex-direction: column;
  margin-bottom: 0.75rem;
}
.drawer-meta {
  font-size: 0.8rem;
  color: var(--arpia-text-muted);
}
.drawer-table-wrap {
  overflow-x: auto;
}
.drawer-table {
  width: 100%;
  font-size: 0.8rem;
  border-collapse: collapse;
}
.drawer-table th,
.drawer-table td {
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid var(--p-surface-200);
  text-align: left;
  white-space: nowrap;
}
.drawer-table th {
  font-weight: 600;
  color: var(--arpia-text-muted);
}
.drawer-actions {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}
.drawer-empty,
.drawer-loading {
  padding: 1rem 0;
  color: var(--arpia-text-muted);
  font-size: 0.9rem;
}
</style>
