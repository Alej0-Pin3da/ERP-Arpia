<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import type { AnticipoDisplay } from './types'
import { formatCOP } from './types'

const props = defineProps<{
  anticiposList: AnticipoDisplay[]
  descontandoAnticipoId: number | null
}>()

const emit = defineEmits<{
  (e: 'nuevo'): void
  (e: 'editar', anticipo: AnticipoDisplay): void
  (e: 'eliminar', anticipo: AnticipoDisplay): void
  (e: 'marcar-descontado', anticipo: AnticipoDisplay): void
}>()

const searchAnticipos = ref('')

const anticiposFiltrados = computed(() => {
  let list = [...props.anticiposList]

  if (searchAnticipos.value.trim()) {
    const q = searchAnticipos.value.trim().toLowerCase()
    list = list.filter(
      (a) =>
        a.nombre_socia.toLowerCase().includes(q) ||
        a.concepto.toLowerCase().includes(q) ||
        (a.comprobante || '').toLowerCase().includes(q),
    )
  }

  return list
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 text-xs font-mono">
      <div class="w-full sm:w-72 relative">
        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-stone-500 text-xs" />
        <InputText
          v-model="searchAnticipos"
          placeholder="Buscar por socia, concepto, recibo..."
          class="w-full pl-8 text-xs font-sans"
        />
      </div>

      <Button
        label="Registrar Nuevo Anticipo"
        icon="pi pi-plus"
        size="small"
        class="p-button-warning text-xs font-semibold whitespace-nowrap"
        @click="emit('nuevo')"
      />
    </div>

    <!-- Anticipos Table (desktop) + Cards (mobile) -->
    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
      <div class="hidden overflow-x-auto md:block">
        <table class="w-full min-w-[760px] text-xs text-left border-collapse font-mono">
          <thead>
            <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] uppercase text-stone-400">
              <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95">Fecha & Socia</th>
              <th class="py-3 px-4 min-w-[180px]">Concepto / Motivo</th>
              <th class="py-3 px-3 text-right whitespace-nowrap">Monto Anticipo</th>
              <th class="py-3 px-3 whitespace-nowrap">Método & Comprobante</th>
              <th class="py-3 px-3 text-center whitespace-nowrap">Estado</th>
              <th class="py-3 px-4 text-center whitespace-nowrap">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60">
            <tr v-for="a in anticiposFiltrados" :key="a.id" class="hover:bg-stone-800/30">
              <td class="py-3.5 px-4 sticky left-0 z-10 bg-stone-900/95">
                <div class="font-serif font-bold text-stone-100 text-xs">{{ a.nombre_socia }}</div>
                <div class="text-[10px] text-stone-400">Fecha: {{ a.fecha }}</div>
              </td>

              <td class="py-3.5 px-4 font-sans text-stone-300 min-w-[180px]">
                <div>{{ a.concepto }}</div>
                <div v-if="a.observaciones" class="text-[10px] text-stone-500 italic mt-0.5">
                  {{ a.observaciones }}
                </div>
              </td>

              <td class="py-3.5 px-3 text-right font-bold text-rose-400 text-sm whitespace-nowrap">
                {{ formatCOP(a.monto) }}
              </td>

              <td class="py-3.5 px-3 text-stone-300 text-[11px]">
                <div>{{ a.metodo_desembolso }}</div>
                <div v-if="a.comprobante" class="text-amber-400/90 font-mono text-[10px]">
                  Ref: {{ a.comprobante }}
                </div>
              </td>

              <td class="py-3.5 px-3 text-center whitespace-nowrap">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                  :class="{
                    'bg-amber-500/20 text-amber-300 border border-amber-500/30': a.estado === 'PENDIENTE_DESCUENTO',
                    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': a.estado === 'DESCONTADO',
                    'bg-rose-950 text-rose-400 border border-rose-800': a.estado === 'ANULADO',
                  }"
                >
                  {{ a.estado === 'PENDIENTE_DESCUENTO' ? '⏳ Pendiente Descuento' : (a.estado === 'DESCONTADO' ? '✅ Descontado' : 'Anulado') }}
                </span>
              </td>

              <td class="py-3.5 px-4 text-center whitespace-nowrap">
                <div class="flex items-center justify-center gap-1">
                  <Button
                    v-if="a.estado === 'PENDIENTE_DESCUENTO'"
                    icon="pi pi-check"
                    size="small"
                    text
                    rounded
                    class="p-button-success text-emerald-400 hover:bg-emerald-950/40"
                    title="Marcar como Descontado"
                    :loading="descontandoAnticipoId === a.id"
                    @click="emit('marcar-descontado', a)"
                  />
                  <Button
                    icon="pi pi-pencil"
                    size="small"
                    text
                    rounded
                    class="p-button-secondary text-stone-300 hover:bg-stone-800"
                    title="Editar Anticipo"
                    @click="emit('editar', a)"
                  />
                  <Button
                    icon="pi pi-trash"
                    size="small"
                    text
                    rounded
                    class="p-button-danger text-rose-400 hover:bg-rose-950/40"
                    title="Eliminar Anticipo"
                    @click="emit('eliminar', a)"
                  />
                </div>
              </td>
            </tr>

            <tr v-if="anticiposFiltrados.length === 0">
              <td colspan="6" class="py-8 text-center text-stone-500">
                <i class="pi pi-inbox text-2xl mb-2 block" />
                No hay registros de anticipos que coincidan.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile cards: same anticiposFiltrados. No horizontal scroll. -->
      <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
        <div v-if="anticiposFiltrados.length === 0" class="text-center py-8 text-sm text-stone-500">
          No hay registros de anticipos que coincidan.
        </div>
        <div v-for="a in anticiposFiltrados" :key="a.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="font-bold text-sm text-stone-100 min-w-0">{{ a.nombre_socia }}</div>
            <span class="text-xs text-stone-500 shrink-0">{{ a.fecha }}</span>
          </div>
          <div class="text-sm text-stone-300">{{ a.concepto }}</div>
          <div v-if="a.observaciones" class="text-sm text-stone-500 italic">{{ a.observaciones }}</div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Monto</span>
            <span class="font-mono font-bold text-rose-400">{{ formatCOP(a.monto) }}</span>
          </div>
          <div class="text-sm text-stone-300">
            {{ a.metodo_desembolso }}
            <span v-if="a.comprobante" class="ml-1 font-mono text-xs text-amber-400/90">Ref: {{ a.comprobante }}</span>
          </div>
          <span
            class="inline-block px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider"
            :class="{
              'bg-amber-500/20 text-amber-300 border border-amber-500/30': a.estado === 'PENDIENTE_DESCUENTO',
              'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': a.estado === 'DESCONTADO',
              'bg-rose-950 text-rose-400 border border-rose-800': a.estado === 'ANULADO',
            }"
          >
            {{ a.estado === 'PENDIENTE_DESCUENTO' ? '⏳ Pendiente Descuento' : (a.estado === 'DESCONTADO' ? '✅ Descontado' : 'Anulado') }}
          </span>
          <div class="flex gap-2 pt-1">
            <button
              v-if="a.estado === 'PENDIENTE_DESCUENTO'"
              type="button"
              class="flex-1 min-h-[40px] rounded-lg bg-emerald-950 text-emerald-300 border border-emerald-800 text-sm font-semibold"
              @click="emit('marcar-descontado', a)"
            >
              Marcar descontado
            </button>
            <button
              type="button"
              class="flex-1 min-h-[40px] rounded-lg bg-stone-800 text-stone-200 text-sm font-semibold"
              @click="emit('editar', a)"
            >
              Editar
            </button>
            <button
              type="button"
              class="min-w-[44px] min-h-[40px] px-3 rounded-lg border border-rose-800 text-rose-400"
              title="Eliminar Anticipo"
              @click="emit('eliminar', a)"
            >
              <i class="pi pi-trash text-xs" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
