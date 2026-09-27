<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import type { LiquidacionDisplay, SociaDisplay } from './types'
import { formatCOP } from './types'

const props = defineProps<{
  liquidaciones: LiquidacionDisplay[]
  sociasReparto: SociaDisplay[]
}>()

const emit = defineEmits<{
  (e: 'nueva'): void
  (e: 'detalle', liquidacion: LiquidacionDisplay): void
  (e: 'eliminar', liquidacion: LiquidacionDisplay): void
  (e: 'cambiar-estado', payload: { liquidacion: LiquidacionDisplay; nuevoEstado: 'BORRADOR' | 'APROBADA' | 'PAGADA' }): void
}>()

const searchLiquidaciones = ref('')
const filterEstadoLiquidacion = ref('TODOS')

function porcentajeSociaReparto(i: number, fallback: number): number {
  const s = props.sociasReparto[i] as any
  return Number(s?.porcentaje ?? s?.porcentaje_participacion ?? fallback) || fallback
}

function itemDistribucion(l: LiquidacionDisplay, sociaId: number | undefined) {
  if (sociaId == null) return undefined
  return l.distribucion.find((d) => d.socia_id === sociaId)
}

const liquidacionesFiltradas = computed(() => {
  let list = [...props.liquidaciones]

  if (searchLiquidaciones.value.trim()) {
    const q = searchLiquidaciones.value.trim().toLowerCase()
    list = list.filter(
      (l) =>
        (l.codigo ?? '').toLowerCase().includes(q) ||
        (l.periodo ?? '').toLowerCase().includes(q) ||
        (l.observaciones ?? '').toLowerCase().includes(q) ||
        (l.distribucion ?? []).some((d) => (d.nombre_socia ?? '').toLowerCase().includes(q)),
    )
  }

  if (filterEstadoLiquidacion.value !== 'TODOS') {
    list = list.filter((l) => l.estado === filterEstadoLiquidacion.value)
  }

  return list
})

function onToggleEstado(l: LiquidacionDisplay) {
  const nuevoEstado = l.estado === 'PAGADA' ? 'BORRADOR' : l.estado === 'BORRADOR' ? 'APROBADA' : 'PAGADA'
  emit('cambiar-estado', { liquidacion: l, nuevoEstado })
}
</script>

<template>
  <div class="space-y-4">
    <!-- Search & Filters -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 text-xs">
      <div class="w-full sm:w-72 relative">
        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-stone-500 text-xs" />
        <InputText
          v-model="searchLiquidaciones"
          placeholder="Buscar por código, periodo, socia..."
          class="w-full pl-8 text-xs"
        />
      </div>

      <div class="flex items-center gap-2 w-full sm:w-auto">
        <span class="text-stone-400 text-xs font-mono">Estado:</span>
        <Dropdown
          v-model="filterEstadoLiquidacion"
          :options="[
            { label: 'Todos los Estados', value: 'TODOS' },
            { label: 'Totalmente Pagadas', value: 'PAGADA' },
            { label: 'Aprobadas', value: 'APROBADA' },
            { label: 'En Borrador', value: 'BORRADOR' },
          ]"
          option-label="label"
          option-value="value"
          class="text-xs w-44"
        />
        <Button
          label="Nueva Liquidación"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold whitespace-nowrap"
          @click="emit('nueva')"
        />
      </div>
    </div>

    <!-- Liquidaciones Table (desktop) + Cards (mobile) -->
    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
      <div class="hidden overflow-x-auto md:block">
        <table class="w-full min-w-[900px] text-xs text-left border-collapse">
          <thead>
            <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] font-mono uppercase text-stone-400">
              <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95">Código & Periodo</th>
              <th class="py-3 px-3 text-right whitespace-nowrap">Ventas Brutas</th>
              <th class="py-3 px-3 text-right whitespace-nowrap">Costos / Gastos</th>
              <th class="py-3 px-3 text-right whitespace-nowrap">Utilidad Neta</th>
              <th class="py-3 px-3 text-center whitespace-nowrap">Fondo Taller (40%)</th>
              <th v-for="(s, i) in sociasReparto" :key="s.id" class="py-3 px-3 text-center whitespace-nowrap">
                {{ s.nombre }} ({{ porcentajeSociaReparto(i, 30) }}%)
              </th>
              <th class="py-3 px-3 text-center whitespace-nowrap">Estado</th>
              <th class="py-3 px-4 text-center whitespace-nowrap">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60 font-mono">
            <tr
              v-for="l in liquidacionesFiltradas"
              :key="l.id"
              class="hover:bg-stone-800/30 transition-colors"
            >
              <td class="py-3.5 px-4 sticky left-0 z-10 bg-stone-900/95">
                <div class="font-bold text-amber-300 font-serif text-sm">{{ l.codigo }}</div>
                <div class="text-stone-200 text-xs font-sans mt-0.5">{{ l.periodo }}</div>
                <div class="text-[10px] text-stone-500">Cierre: {{ l.fecha_cierre }}</div>
              </td>

              <td class="py-3.5 px-3 text-right font-bold text-stone-100 whitespace-nowrap">
                {{ formatCOP(l.total_ventas_brutas) }}
              </td>

              <td class="py-3.5 px-3 text-right text-stone-400 text-[11px] whitespace-nowrap">
                <div>-{{ formatCOP(l.costo_taller_insumos) }} ins.</div>
                <div>-{{ formatCOP(l.gastos_operativos) }} gast.</div>
              </td>

              <td class="py-3.5 px-3 text-right font-bold text-emerald-400 text-sm whitespace-nowrap">
                {{ formatCOP(l.utilidad_neta_total) }}
              </td>

              <td class="py-3.5 px-3 text-center">
                <span class="text-amber-300 font-bold text-xs">{{ formatCOP(l.fondo_reinversion_monto) }}</span>
              </td>

              <td v-for="(s) in sociasReparto" :key="s.id" class="py-3.5 px-3 text-center">
                <div class="text-stone-200 font-semibold text-xs">
                  {{ formatCOP(itemDistribucion(l, s.id)?.monto_neto_pagar || 0) }}
                </div>
                <span
                  class="text-[9px] px-1.5 py-0.2 rounded"
                  :class="itemDistribucion(l, s.id)?.estado_pago === 'PAGADO' ? 'bg-emerald-950 text-emerald-400' : 'bg-stone-800 text-amber-400'"
                >
                  {{ itemDistribucion(l, s.id)?.estado_pago || 'PENDIENTE' }}
                </span>
              </td>

              <td class="py-3.5 px-3 text-center">
                <button
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider cursor-pointer hover:opacity-80 transition-opacity"
                  :class="{
                    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': l.estado === 'PAGADA',
                    'bg-amber-500/20 text-amber-300 border border-amber-500/30': l.estado === 'APROBADA',
                    'bg-stone-800 text-stone-400 border border-stone-700': l.estado === 'BORRADOR',
                  }"
                  :title="'Click para cambiar estado (actual: ' + l.estado + ')'"
                  @click="onToggleEstado(l)"
                >
                  {{ l.estado }}
                </button>
              </td>

              <td class="py-3.5 px-4 text-center">
                <div class="flex items-center justify-center gap-1.5">
                  <Button
                    icon="pi pi-eye"
                    size="small"
                    text
                    rounded
                    class="p-button-secondary text-amber-300 hover:bg-stone-800"
                    title="Ver Acta Oficial & Transferencias"
                    @click="emit('detalle', l)"
                  />
                  <Button
                    icon="pi pi-trash"
                    size="small"
                    text
                    rounded
                    class="p-button-danger text-rose-400 hover:bg-rose-950/40"
                    title="Eliminar Liquidación"
                    @click="emit('eliminar', l)"
                  />
                </div>
              </td>
            </tr>

            <tr v-if="liquidacionesFiltradas.length === 0">
              <td colspan="9" class="py-8 text-center text-stone-500">
                <i class="pi pi-inbox text-2xl mb-2 block" />
                No se encontraron liquidaciones de socias con los filtros actuales.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile cards: same liquidacionesFiltradas. No horizontal scroll. -->
      <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
        <div v-if="liquidacionesFiltradas.length === 0" class="text-center py-8 text-sm text-stone-500">
          No se encontraron liquidaciones de socias con los filtros actuales.
        </div>
        <div v-for="l in liquidacionesFiltradas" :key="l.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="min-w-0">
              <div class="font-bold text-sm text-amber-300">{{ l.codigo }}</div>
              <div class="text-sm text-stone-200">{{ l.periodo }}</div>
              <div class="text-xs text-stone-500">Cierre: {{ l.fecha_cierre }}</div>
            </div>
            <button
              type="button"
              class="px-2 py-1 rounded-full text-xs font-bold uppercase tracking-wider shrink-0 min-h-[40px]"
              :class="{
                'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': l.estado === 'PAGADA',
                'bg-amber-500/20 text-amber-300 border border-amber-500/30': l.estado === 'APROBADA',
                'bg-stone-800 text-stone-400 border border-stone-700': l.estado === 'BORRADOR',
              }"
              @click="onToggleEstado(l)"
            >
              {{ l.estado }}
            </button>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Ventas brutas</span>
            <span class="font-mono font-bold text-stone-100">{{ formatCOP(l.total_ventas_brutas) }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Costos / gastos</span>
            <span class="font-mono text-stone-400">−{{ formatCOP(l.costo_taller_insumos) }} / −{{ formatCOP(l.gastos_operativos) }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Utilidad neta</span>
            <span class="font-mono font-bold text-emerald-400">{{ formatCOP(l.utilidad_neta_total) }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Fondo taller (40%)</span>
            <span class="font-mono font-bold text-amber-300">{{ formatCOP(l.fondo_reinversion_monto) }}</span>
          </div>
          <div class="space-y-1 border-t border-stone-800 pt-2">
            <div v-for="(s, i) in sociasReparto" :key="s.id" class="flex items-center justify-between text-sm">
              <span class="text-stone-300">{{ s.nombre }} ({{ porcentajeSociaReparto(i, 30) }}%)</span>
              <span class="font-mono font-semibold text-stone-100">{{ formatCOP(itemDistribucion(l, s.id)?.monto_neto_pagar || 0) }}</span>
            </div>
          </div>
          <div class="flex gap-2 pt-1">
            <button
              type="button"
              class="flex-1 min-h-[40px] rounded-lg bg-stone-800 text-amber-300 text-sm font-semibold"
              @click="emit('detalle', l)"
            >
              Ver acta
            </button>
            <button
              type="button"
              class="min-w-[44px] min-h-[40px] px-3 rounded-lg border border-rose-800 text-rose-400"
              title="Eliminar Liquidación"
              @click="emit('eliminar', l)"
            >
              <i class="pi pi-trash text-xs" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
