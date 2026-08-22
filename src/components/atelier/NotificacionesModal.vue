<script setup lang="ts">
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'ir-insumos'): void
}>()
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="🔔 Notificaciones de Operaciones • Atelier"
    :style="{ width: '90vw', maxWidth: '480px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-3 pt-1">
      <div class="bg-stone-900/80 border border-amber-500/30 rounded-xl p-3 text-xs flex items-start gap-3">
        <div class="w-7 h-7 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center flex-shrink-0 font-bold">
          ⚠️
        </div>
        <div class="space-y-1">
          <div class="font-bold text-stone-100">Stock Crítico: Lino Vértigo (4.5 m)</div>
          <div class="text-stone-400 leading-relaxed">
            Quedan 4.5m disponibles y el mínimo para corsetería es de 6m. Se sugiere emitir orden a Kilotelas.
          </div>
          <button
            type="button"
            class="text-amber-400 hover:underline font-bold text-[11px] pt-1 block"
            @click="emit('ir-insumos'); emit('update:visible', false)"
          >
            Ver en Inventario →
          </button>
        </div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-xl p-3 text-xs flex items-start gap-3">
        <div class="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0 font-bold">
          ✂️
        </div>
        <div class="space-y-1">
          <div class="font-bold text-stone-100">Prenda en Fase de Costura</div>
          <div class="text-stone-400 leading-relaxed">
            Orden #ORD-ARP-006 (Valentina Restrepo - Blusa Malla Garra) se encuentra actualmente en costura.
          </div>
        </div>
      </div>

      <div class="flex justify-end pt-2">
        <Button label="Entendido" severity="secondary" size="small" @click="emit('update:visible', false)" />
      </div>
    </div>
  </Dialog>
</template>
