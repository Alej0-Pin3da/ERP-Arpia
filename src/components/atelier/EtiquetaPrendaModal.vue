<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { showToast } from '@/utils/toast'
import { updateProducto } from '@/services/api/productos'

/** Minimal shapes this modal reads (REAL display objects from the caller). */
export interface EtiquetaPrenda {
  codigo: string
  nombre: string
  precio_venta: number
  coleccion?: string | null
  composicion?: string | null
}
export interface EtiquetaVariante {
  talla: string
  sku?: string
  color?: string
  composicion?: string
  lote?: string
}

const COLECCION_DEFAULT = 'Colección Eterna'

const props = defineProps<{
  visible: boolean
  prenda: EtiquetaPrenda | null
  variante: EtiquetaVariante | null
  /** Lote flow: producto id for persisting coleccion/composicion. */
  productoId?: number | null
  /** Lote flow: finished units — informational, shown OUTSIDE the tag, never as talla/color. */
  cantidad?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardado', payload: { coleccion: string | null; composicion: string | null }): void
}>()

/** Editable inputs (dialog, OUTSIDE the printable tag). Tag mockup reads these. */
const coleccionInput = ref(COLECCION_DEFAULT)
const composicionInput = ref('')
const tallaInput = ref('')
const colorInput = ref('')
const saving = ref(false)

function resetInputs() {
  coleccionInput.value = props.prenda?.coleccion || COLECCION_DEFAULT
  composicionInput.value = props.prenda?.composicion || props.variante?.composicion || ''
  // Legacy synthetic lote variante used talla 'Lote' / color 'N uds' — never carry that over.
  const rawTalla = props.variante?.talla || ''
  tallaInput.value = rawTalla.toLowerCase() === 'lote' ? '' : rawTalla
  const rawColor = props.variante?.color || ''
  colorInput.value = /uds/i.test(rawColor) ? '' : rawColor
}

watch(() => props.visible, (open) => { if (open) resetInputs() })
watch(() => props.prenda, () => { if (props.visible) resetInputs() })

const serialNumber = computed(() => {
  if (!props.prenda) return '—'
  const tallaPart = tallaInput.value || props.variante?.talla || 'Lote'
  const sufijo = props.variante?.sku?.slice(-4) || props.prenda.codigo.slice(-4) || '—'
  return `${props.prenda.codigo}-${tallaPart}-${sufijo}`
})

// REAL-only: sin prenda real no se puede imprimir (la variante es opcional:
// el flujo lote no tiene talla/color unitarios — se muestran como '—').
const datosCompletos = computed(() => Boolean(props.prenda?.codigo && props.prenda?.nombre))

function formatCOP(val: number | string) {
  return `$${Math.round(Number(val ?? 0)).toLocaleString('es-CO')}`
}

async function guardarEnProducto() {
  if (props.productoId == null) {
    showToast('warn', 'Sin producto', 'La etiqueta no trae productoId: no hay dónde guardar.')
    return
  }
  saving.value = true
  try {
    const updated = await updateProducto(props.productoId, {
      coleccion: coleccionInput.value.trim() || null,
      composicion: composicionInput.value.trim() || null,
    })
    coleccionInput.value = updated.coleccion || COLECCION_DEFAULT
    composicionInput.value = updated.composicion || ''
    // Tag already reads the inputs; notify the caller so ITS state stays in sync (no prop mutation).
    emit('guardado', { coleccion: updated.coleccion ?? null, composicion: updated.composicion ?? null })
    showToast('success', 'Guardado', `Colección y composición guardadas en ${props.prenda?.nombre ?? 'el producto'}.`)
  } catch (e) {
    console.error('Error guardando colección/composición:', e)
    showToast('error', 'No se pudo guardar', 'Revisá la conexión con el backend e intentá de nuevo.')
  } finally {
    saving.value = false
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
      <!-- Lote units: informational, OUTSIDE the printable tag (never talla/color). -->
      <div v-if="props.cantidad != null" class="mx-auto w-full max-w-sm rounded-xl bg-sky-950/60 border border-sky-500/30 px-3 py-2 text-center font-mono text-xs text-sky-300">
        Lote de {{ Math.round(Number(props.cantidad)) }} uds · informativo, no se imprime
      </div>

      <!-- Editable fields (dialog only, outside the printable tag) -->
      <div class="mx-auto w-full max-w-sm rounded-2xl border border-stone-800 bg-stone-900/60 p-4 space-y-3">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1 min-w-0">
            <label for="etq-coleccion" class="text-[11px] font-bold uppercase tracking-wider text-stone-400">Colección</label>
            <InputText id="etq-coleccion" v-model="coleccionInput" class="w-full text-xs" placeholder="Colección Eterna" />
          </div>
          <div class="space-y-1 min-w-0">
            <label for="etq-composicion" class="text-[11px] font-bold uppercase tracking-wider text-stone-400">Composición textil</label>
            <InputText id="etq-composicion" v-model="composicionInput" class="w-full text-xs" placeholder="Ej: 100% algodón" />
          </div>
          <div class="space-y-1 min-w-0">
            <label for="etq-talla" class="text-[11px] font-bold uppercase tracking-wider text-stone-400">Talla</label>
            <InputText id="etq-talla" v-model="tallaInput" class="w-full text-xs" placeholder="—" />
          </div>
          <div class="space-y-1 min-w-0">
            <label for="etq-color" class="text-[11px] font-bold uppercase tracking-wider text-stone-400">Color</label>
            <InputText id="etq-color" v-model="colorInput" class="w-full text-xs" placeholder="—" />
          </div>
        </div>
        <Button
          label="Guardar en producto"
          icon="pi pi-save"
          size="small"
          severity="secondary"
          outlined
          class="text-xs w-full"
          :loading="saving"
          :disabled="props.productoId == null || saving"
          title="Persiste colección y composición en el producto"
          @click="guardarEnProducto"
        />
      </div>

      <!-- Tag Physical Mockup (Front & Back Luxury Tag) — ONLY this prints. -->
      <div id="luxury-garment-tag" class="mx-auto w-full max-w-sm rounded-2xl bg-stone-950 border-2 border-amber-500/40 p-6 text-stone-100 shadow-2xl relative overflow-hidden flex flex-col items-center text-center space-y-4">
        <!-- Tag Hanging Eyelet -->
        <div class="w-4 h-4 rounded-full bg-stone-900 border-2 border-amber-500/60 shadow-inner -mt-2 flex items-center justify-center">
          <div class="w-1.5 h-1.5 rounded-full bg-stone-950" />
        </div>

        <!-- Brand Emblem -->
        <div class="space-y-1">
          <div class="text-xs font-mono tracking-[0.3em] uppercase text-amber-400 font-bold">
            A R P Í A
          </div>
          <div class="text-[10px] font-serif italic text-stone-400">
            HECHO POR GARRAS COLOMBIANAS
          </div>
        </div>

        <div class="w-full h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent" />

        <!-- Garment Details -->
        <div class="space-y-1">
          <h3 class="text-base font-serif font-bold text-stone-100 m-0">
            {{ props.prenda?.nombre || '—' }}
          </h3>
          <div v-if="!props.prenda" class="text-xs text-stone-500 font-mono">
            Sin registro — pendiente: se requiere la prenda real.
          </div>
          <div class="text-xs text-amber-300/90 font-mono">
            {{ coleccionInput || '—' }} · Hecho a Mano en Colombia
          </div>
        </div>

        <!-- Size & Specs Box -->
        <div class="grid grid-cols-3 gap-2 w-full font-mono text-xs pt-1">
          <div class="bg-stone-900/90 border border-stone-800 p-2 rounded-lg">
            <span class="text-[9px] text-stone-400 block uppercase">Talla</span>
            <span class="font-bold text-amber-300 text-sm">{{ tallaInput || '—' }}</span>
          </div>
          <div class="bg-stone-900/90 border border-stone-800 p-2 rounded-lg">
            <span class="text-[9px] text-stone-400 block uppercase">Color</span>
            <span class="font-bold text-stone-200 text-xs">{{ colorInput || '—' }}</span>
          </div>
          <div class="bg-stone-900/90 border border-stone-800 p-2 rounded-lg">
            <span class="text-[9px] text-stone-400 block uppercase">Precio PVP</span>
            <span class="font-bold text-emerald-400 text-xs">{{ props.prenda ? formatCOP(props.prenda?.precio_venta || 0) : '—' }}</span>
          </div>
        </div>

        <!-- Textile Composition & Care Icons -->
        <div class="bg-stone-900/50 border border-stone-800/80 rounded-xl p-3 w-full text-left space-y-1.5 text-[11px] font-mono text-stone-300">
          <div class="flex items-center justify-between text-stone-400 text-[10px]">
            <span>COMPOSICIÓN TEXTIL:</span>
            <span class="text-amber-400 font-bold">{{ composicionInput || '—' }}</span>
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
          <!-- QR placeholder: static preview, not scannable -->
          <div class="w-16 h-16 bg-white p-1 rounded-lg shadow flex items-center justify-center" title="Vista previa — código ilustrativo, no escaneable">
            <svg viewBox="0 0 24 24" class="w-full h-full text-stone-950">
              <path fill="currentColor" d="M2 2h8v8H2V2zm2 2v4h4V4H4zm10-2h8v8h-8V2zm2 2v4h4V4h-4zM2 14h8v8H2v-8zm2 2v4h4v-4H4zm12 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-4 4h2v2h-2v-2zm4 0h2v2h-2v-2zm-6-4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
            </svg>
          </div>

          <div class="text-right space-y-0.5">
            <div class="text-[9px] text-stone-400 uppercase">Número de Serie Único:</div>
            <div class="text-xs text-amber-400 font-bold">{{ serialNumber }}</div>
            <div class="text-[9px] text-stone-500">{{ props.variante?.lote || props.prenda?.codigo || 'Sin registro — pendiente' }}</div>
          </div>
        </div>

        <div class="w-full text-center text-[9px] font-mono text-stone-500">Vista previa: el código es ilustrativo, no escaneable.</div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-start w-full pt-3 border-t border-stone-800">
        <Button
          label="Cerrar"
          icon="pi pi-times"
          size="small"
          severity="secondary"
          outlined
          class="text-xs"
          @click="emit('update:visible', false)"
        />
      </div>
    </template>
  </Dialog>
</template>

