<script setup lang="ts">
import { computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { type PrendaConfeccionada, type PrendaVariante } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  prenda: PrendaConfeccionada | null
  variante: PrendaVariante | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const serialNumber = computed(() => {
  if (!props.prenda || !props.variante) return 'ARP-2026-0001'
  return `${props.prenda.codigo}-${props.variante.talla}-${props.variante.sku.slice(-4)}`
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function imprimirEtiqueta() {
  showToast('success', 'Imprimiendo Etiqueta', `Enviando etiqueta de ${props.prenda?.nombre} a la impresora de taller.`)
  if (typeof window !== 'undefined') {
    window.print()
  }
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    modal
    header="Etiqueta de Autor & Certificado de Autenticidad"
    :style="{ width: '560px', maxWidth: '95vw' }"
    class="p-dialog-arpia"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="space-y-6 pt-2">
      <!-- Tag Physical Mockup (Front & Back Luxury Tag) -->
      <div id="luxury-garment-tag" class="mx-auto w-full max-w-sm rounded-2xl bg-stone-950 border-2 border-amber-500/40 p-6 text-stone-100 shadow-2xl relative overflow-hidden flex flex-col items-center text-center space-y-4">
        <!-- Tag Hanging Eyelet -->
        <div class="w-4 h-4 rounded-full bg-stone-900 border-2 border-amber-500/60 shadow-inner -mt-2 flex items-center justify-center">
          <div class="w-1.5 h-1.5 rounded-full bg-stone-950" />
        </div>

        <!-- Atelier Brand Emblem -->
        <div class="space-y-1">
          <div class="text-xs font-mono tracking-[0.3em] uppercase text-amber-400 font-bold">
            A R P Í A
          </div>
          <div class="text-[10px] font-serif italic text-stone-400">
            Atelier de Alta Costura & Corsetería
          </div>
        </div>

        <div class="w-full h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent" />

        <!-- Garment Details -->
        <div class="space-y-1">
          <h3 class="text-base font-serif font-bold text-stone-100 m-0">
            {{ props.prenda?.nombre || 'Corset de Alta Costura' }}
          </h3>
          <div class="text-xs text-amber-300/90 font-mono">
            Colección Eterna · Hecho a Mano en Colombia
          </div>
        </div>

        <!-- Size & Specs Box -->
        <div class="grid grid-cols-3 gap-2 w-full font-mono text-xs pt-1">
          <div class="bg-stone-900/90 border border-stone-800 p-2 rounded-lg">
            <span class="text-[9px] text-stone-400 block uppercase">Talla</span>
            <span class="font-bold text-amber-300 text-sm">{{ props.variante?.talla || 'M' }}</span>
          </div>
          <div class="bg-stone-900/90 border border-stone-800 p-2 rounded-lg">
            <span class="text-[9px] text-stone-400 block uppercase">Color</span>
            <span class="font-bold text-stone-200 text-xs">{{ props.variante?.color || 'Noir' }}</span>
          </div>
          <div class="bg-stone-900/90 border border-stone-800 p-2 rounded-lg">
            <span class="text-[9px] text-stone-400 block uppercase">Precio PVP</span>
            <span class="font-bold text-emerald-400 text-xs">{{ formatCOP(props.prenda?.precio_venta || 0) }}</span>
          </div>
        </div>

        <!-- Textile Composition & Care Icons -->
        <div class="bg-stone-900/50 border border-stone-800/80 rounded-xl p-3 w-full text-left space-y-1.5 text-[11px] font-mono text-stone-300">
          <div class="flex items-center justify-between text-stone-400 text-[10px]">
            <span>COMPOSICIÓN TEXTIL:</span>
            <span class="text-amber-400 font-bold">100% SEDA & ACERO</span>
          </div>
          <div class="text-[10px] text-stone-300 leading-snug">
            92% Satín Duquesa de Seda · 8% Elastano · Varillas de Acero Espiralado Inoxidable
          </div>

          <!-- Laundry Icons mockup -->
          <div class="flex items-center justify-around pt-2 text-stone-400 text-xs border-t border-stone-800/60">
            <span title="Lavado en seco profesional">🧼 Lavado en Seco</span>
            <span title="No usar lejía">🚫 No Cloro</span>
            <span title="Planchado bajo">🔥 Plancha Baja</span>
          </div>
        </div>

        <!-- Serial QR Code & Barcode SVG -->
        <div class="w-full flex items-center justify-between pt-1 font-mono">
          <!-- QR SVG Mockup -->
          <div class="w-16 h-16 bg-white p-1 rounded-lg shadow flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="w-full h-full text-stone-950">
              <path fill="currentColor" d="M2 2h8v8H2V2zm2 2v4h4V4H4zm10-2h8v8h-8V2zm2 2v4h4V4h-4zM2 14h8v8H2v-8zm2 2v4h4v-4H4zm12 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-4 4h2v2h-2v-2zm4 0h2v2h-2v-2zm-6-4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
            </svg>
          </div>

          <div class="text-right space-y-0.5">
            <div class="text-[9px] text-stone-400 uppercase">Número de Serie Único:</div>
            <div class="text-xs text-amber-400 font-bold">{{ serialNumber }}</div>
            <div class="text-[9px] text-stone-500">Taller Arpía Pereira · Lote 2026-A</div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full pt-3 border-t border-stone-800">
        <Button
          label="Cerrar"
          icon="pi pi-times"
          size="small"
          severity="secondary"
          outlined
          class="text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          label="Imprimir Etiqueta Térmica / PDF"
          icon="pi pi-print"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="imprimirEtiqueta"
        />
      </div>
    </template>
  </Dialog>
</template>
