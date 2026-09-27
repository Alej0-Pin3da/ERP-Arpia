<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import type { SociaDisplay, LiquidacionDisplay, AnticipoDisplay } from './types'
import { formatCOP } from './types'

const props = defineProps<{
  sociasList: SociaDisplay[]
  liquidacionesList: LiquidacionDisplay[]
  anticiposList: AnticipoDisplay[]
}>()

const emit = defineEmits<{
  (e: 'nueva'): void
  (e: 'editar', socia: SociaDisplay): void
  (e: 'eliminar', socia: SociaDisplay): void
  (e: 'toggle-activo', socia: SociaDisplay): void
}>()

const sumaPorcentajesSocias = computed(() => {
  return props.sociasList.filter((s) => s.activo).reduce((acc, s) => acc + s.porcentaje, 0)
})

function getIngresoHistoricoSocia(sociaId: number): number {
  return props.liquidacionesList.reduce((acc, l) => {
    const item = l.distribucion.find((d) => d.socia_id === sociaId)
    return acc + (item ? item.monto_neto_pagar : 0)
  }, 0)
}

function getAnticiposPendientesSocia(sociaId: number): number {
  return props.anticiposList
    .filter((a) => a.socia_id === sociaId && a.estado === 'PENDIENTE_DESCUENTO')
    .reduce((acc, a) => acc + a.monto, 0)
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
      <div>
        <div class="text-xs font-bold text-amber-300 uppercase font-mono">
          Estructura de Socias & Porcentajes de Participación
        </div>
        <div class="text-[11px] text-stone-400 font-mono mt-0.5">
          Suma total activa: <strong class="text-emerald-400">{{ sumaPorcentajesSocias }}%</strong>
          (Según porcentajes registrados de socias activas)
        </div>
      </div>

      <Button
        label="Añadir Nueva Socia"
        icon="pi pi-user-plus"
        size="small"
        class="p-button-warning text-xs font-semibold"
        @click="emit('nueva')"
      />
    </div>

    <!-- Socias Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div
        v-for="s in sociasList"
        :key="s.id"
        class="rounded-2xl border bg-stone-900/60 p-5 relative overflow-hidden flex flex-col justify-between transition-all"
        :class="s.activo ? 'border-stone-800 hover:border-amber-500/40' : 'border-stone-800/40 opacity-60'"
      >
        <div>
          <div class="flex items-center justify-between">
            <span class="px-2.5 py-1 rounded-full text-xs font-mono font-bold text-amber-300 bg-amber-500/20 border border-amber-500/30">
              {{ s.porcentaje }}% Participación
            </span>
            <span
              class="text-[10px] px-2 py-0.5 rounded font-mono font-bold"
              :class="s.activo ? 'bg-emerald-950 text-emerald-400' : 'bg-stone-800 text-stone-400'"
            >
              {{ s.activo ? 'Activa' : 'Inactiva' }}
            </span>
          </div>

          <div class="font-serif font-bold text-stone-100 text-base mt-3">{{ s.nombre }}</div>
          <div class="text-xs text-stone-400 font-mono mt-0.5">{{ s.rol }}</div>

          <div class="mt-4 pt-3 border-t border-stone-800/80 space-y-2 text-xs font-mono text-stone-300">
            <div class="flex items-center justify-between text-[11px]">
              <span class="text-stone-500">Banco / Plataforma:</span>
              <span class="font-bold text-stone-200">{{ s.banco || 'N/A' }}</span>
            </div>
            <div class="flex items-center justify-between text-[11px]">
              <span class="text-stone-500">N° Cuenta:</span>
              <span class="text-stone-300">{{ s.numero_cuenta || 'N/A' }} ({{ s.tipo_cuenta || 'Ahorros' }})</span>
            </div>
            <div v-if="s.telefono" class="flex items-center justify-between text-[11px]">
              <span class="text-stone-500">Teléfono:</span>
              <span class="text-stone-300">{{ s.telefono }}</span>
            </div>
            <div v-if="s.email" class="flex items-center justify-between text-[11px]">
              <span class="text-stone-500">Email:</span>
              <span class="text-stone-300 truncate max-w-[150px]">{{ s.email }}</span>
            </div>
          </div>

          <!-- Historical Financials -->
          <div class="mt-4 p-3 rounded-xl bg-stone-950/80 border border-stone-800/80 font-mono space-y-1.5">
            <div class="flex items-center justify-between text-[11px]">
              <span class="text-stone-400">Total Liquidado Histórico:</span>
              <span class="text-emerald-400 font-bold">{{ formatCOP(getIngresoHistoricoSocia(s.id)) }}</span>
            </div>
            <div class="flex items-center justify-between text-[11px]">
              <span class="text-stone-400">Anticipos Pendientes:</span>
              <span class="text-rose-400 font-bold">{{ formatCOP(getAnticiposPendientesSocia(s.id)) }}</span>
            </div>
          </div>

          <p v-if="s.notas" class="text-[11px] text-stone-400 italic mt-3 line-clamp-2">
            "{{ s.notas }}"
          </p>
        </div>

        <div class="mt-5 pt-3 border-t border-stone-800 flex items-center justify-between">
          <Button
            :label="s.activo ? 'Desactivar' : 'Activar'"
            size="small"
            text
            class="text-[11px] p-0 text-stone-400 hover:text-stone-200"
            @click="emit('toggle-activo', s)"
          />

          <div class="flex items-center gap-1">
            <Button
              icon="pi pi-pencil"
              size="small"
              text
              rounded
              class="p-button-secondary text-amber-300 hover:bg-stone-800"
              @click="emit('editar', s)"
            />
            <Button
              v-if="!s.es_fondo_taller"
              icon="pi pi-trash"
              size="small"
              text
              rounded
              class="p-button-danger text-rose-400 hover:bg-rose-950/40"
              @click="emit('eliminar', s)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
