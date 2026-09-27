<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import type { MovimientoRead } from '@/services/api/movimientos'
import { formatCOP } from './types'

const props = defineProps<{
  movimientosList: MovimientoRead[]
}>()

const emit = defineEmits<{
  (e: 'recargar', filters: { tipo?: string; estado?: string }): void
}>()

const filterMovTipo = ref('TODOS')
const filterMovEstado = ref('TODOS')

const movimientosFiltrados = computed(() => {
  let list = [...props.movimientosList]
  if (filterMovTipo.value !== 'TODOS') {
    list = list.filter((m) => m.tipo === filterMovTipo.value)
  }
  if (filterMovEstado.value !== 'TODOS') {
    list = list.filter((m) => m.estado === filterMovEstado.value)
  }
  return list
})

function onRecargar() {
  emit('recargar', {
    tipo: filterMovTipo.value !== 'TODOS' ? filterMovTipo.value : undefined,
    estado: filterMovEstado.value !== 'TODOS' ? filterMovEstado.value : undefined,
  })
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 text-xs font-mono">
      <div class="flex items-center gap-2 w-full sm:w-auto">
        <span class="text-stone-400 text-xs font-mono">Tipo:</span>
        <Dropdown
          v-model="filterMovTipo"
          :options="[
            { label: 'Todos', value: 'TODOS' },
            { label: 'Gasto', value: 'Gasto' },
            { label: 'Inversión', value: 'Inversion' },
            { label: 'Retiro', value: 'Retiro' },
          ]"
          option-label="label"
          option-value="value"
          class="text-xs w-36"
          @change="onRecargar"
        />
        <span class="text-stone-400 text-xs font-mono">Estado:</span>
        <Dropdown
          v-model="filterMovEstado"
          :options="[
            { label: 'Todos', value: 'TODOS' },
            { label: 'Borrador', value: 'draft' },
            { label: 'Confirmado', value: 'confirmed' },
            { label: 'Anulado', value: 'cancelled' },
            { label: 'Revertido', value: 'reversed' },
          ]"
          option-label="label"
          option-value="value"
          class="text-xs w-36"
          @change="onRecargar"
        />
      </div>
      <Button
        label="Recargar"
        icon="pi pi-refresh"
        size="small"
        severity="secondary"
        outlined
        class="text-xs"
        @click="onRecargar"
      />
    </div>

    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
      <div class="hidden overflow-x-auto md:block">
        <table class="w-full min-w-[640px] text-xs text-left border-collapse font-mono">
          <thead>
            <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] uppercase text-stone-400">
              <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95 whitespace-nowrap">Fecha</th>
              <th class="py-3 px-4 whitespace-nowrap">Tipo</th>
              <th class="py-3 px-4 min-w-[180px]">Descripción</th>
              <th class="py-3 px-3 text-right whitespace-nowrap">Monto</th>
              <th class="py-3 px-3 text-center whitespace-nowrap">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60">
            <tr v-for="m in movimientosFiltrados" :key="m.id" class="hover:bg-stone-800/30">
              <td class="py-3 px-4 text-stone-300 sticky left-0 z-10 bg-stone-900/95 whitespace-nowrap">{{ m.fecha }}</td>
              <td class="py-3 px-4 text-amber-300 font-bold whitespace-nowrap">{{ m.tipo }}</td>
              <td class="py-3 px-4 text-stone-300 min-w-[180px]">{{ m.descripcion }}</td>
              <td class="py-3 px-3 text-right font-bold text-stone-100 whitespace-nowrap">{{ formatCOP(Number(m.monto ?? 0)) }}</td>
              <td class="py-3 px-3 text-center whitespace-nowrap">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
                  :class="m.estado === 'confirmed' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : m.estado === 'draft' ? 'bg-stone-800 text-stone-400 border-stone-700' : 'bg-rose-950 text-rose-400 border-rose-800'"
                >
                  {{ m.estado }}
                </span>
              </td>
            </tr>
            <tr v-if="!movimientosFiltrados.length">
              <td colspan="5" class="py-8 text-center text-stone-500">
                <i class="pi pi-inbox text-2xl mb-2 block" />
                Sin movimientos con los filtros actuales.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile cards: same movimientosFiltrados. No horizontal scroll. -->
      <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
        <div v-if="!movimientosFiltrados.length" class="text-center py-8 text-sm text-stone-500">
          Sin movimientos con los filtros actuales.
        </div>
        <div v-for="m in movimientosFiltrados" :key="m.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="font-bold text-sm text-amber-300 min-w-0">{{ m.tipo }}</div>
            <span class="text-xs text-stone-500 shrink-0">{{ m.fecha }}</span>
          </div>
          <div class="text-sm text-stone-300">{{ m.descripcion }}</div>
          <div class="flex items-center justify-between text-sm">
            <span
              class="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border"
              :class="m.estado === 'confirmed' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : m.estado === 'draft' ? 'bg-stone-800 text-stone-400 border-stone-700' : 'bg-rose-950 text-rose-400 border-rose-800'"
            >
              {{ m.estado }}
            </span>
            <span class="font-mono font-bold text-stone-100">{{ formatCOP(Number(m.monto ?? 0)) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
