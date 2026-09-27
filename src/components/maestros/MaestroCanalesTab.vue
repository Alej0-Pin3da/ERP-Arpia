<script setup lang="ts">
import { ref } from 'vue'
import InputNumber from 'primevue/inputnumber'
import type { CanalRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'
import { showToast } from '@/utils/toast'
import { getApiErrorDetail } from '@/utils/api-error'

defineProps<{
  canales: CanalRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', payload: { tipo: string; id: number; nombre: string }): void
}>()

const maestros = useMaestros()

const modalCanal = ref(false)
const modoEdicionCanal = ref(false)
const canalForm = ref<Partial<CanalRead>>({
  nombre: '',
  tipo: 'DIGITAL',
  comision_pct: 0,
  costo_fijo_mensual: 0,
  activo: true,
  descripcion: '',
})

function sanitizeCanalPayload(form: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const nombre = String(form.nombre ?? '').trim()
  if (nombre) out.nombre = nombre
  let codigo = String(form.codigo ?? '').trim()
  if (!codigo && nombre) {
    codigo = nombre.toUpperCase().replace(/\s+/g, '_').replace(/[^A-Z0-9_]/g, '').slice(0, 50) || 'CANAL'
  }
  if (codigo) out.codigo = codigo
  const tipoRaw = String(form.tipo ?? '').trim().toUpperCase()
  if (['FISICO', 'DIGITAL', 'EVENTO'].includes(tipoRaw)) out.tipo = tipoRaw
  else out.tipo = 'DIGITAL'
  const com = form.comision_pct
  if (com !== '' && com !== null && com !== undefined) {
    const n = Number(com)
    if (!Number.isNaN(n)) out.comision_pct = Math.max(0, Math.min(100, n))
  }
  const costo = form.costo_fijo_mensual
  if (costo !== '' && costo !== null && costo !== undefined) {
    const n = Number(costo)
    if (!Number.isNaN(n)) out.costo_fijo_mensual = Math.max(0, n)
  }
  out.activo = form.activo !== false
  const desc = String(form.descripcion ?? '').trim()
  out.descripcion = desc || null
  return out
}

function abrirNuevoCanal() {
  modoEdicionCanal.value = false
  canalForm.value = {
    nombre: '',
    tipo: 'DIGITAL',
    comision_pct: 0,
    costo_fijo_mensual: 0,
    activo: true,
    descripcion: '',
  }
  modalCanal.value = true
}

function abrirEditarCanal(c: CanalRead) {
  modoEdicionCanal.value = true
  canalForm.value = { ...c }
  modalCanal.value = true
}

async function guardarCanal() {
  if (!canalForm.value.nombre) {
    showToast('warn', 'Campo requerido', 'Ingresá el nombre del canal.')
    return
  }
  const payload = sanitizeCanalPayload(canalForm.value as unknown as Record<string, unknown>)
  try {
    if (modoEdicionCanal.value && canalForm.value.id) {
      await maestros.updateCanal(canalForm.value.id, payload)
    } else {
      await maestros.createCanal(payload)
    }
    emit('actualizado')
    showToast('success', 'Canal guardado', `${canalForm.value.nombre} guardado correctamente.`)
    modalCanal.value = false
  } catch (e: unknown) {
    showToast('error', 'Error 422', getApiErrorDetail(e, 'Error al guardar canal', ', '))
  }
}

function formatoCOP(val: number | string | undefined | null) {
  const n = Number(val || 0)
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(n)
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
      <div>
        <h2 class="text-lg font-serif font-bold text-stone-100">Canales de Comercialización & Eventos</h2>
        <p class="text-xs text-stone-400 font-mono">Puntos de venta propios, redes sociales, stands en convenciones y boutiques multimarca.</p>
      </div>

      <button
        id="btn-nuevo-canal"
        @click="abrirNuevoCanal"
        class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
      >
        <span>+</span> Nuevo Canal
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="canal in canales"
        :key="canal.id"
        :id="`card-canal-${canal.id}`"
        class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
      >
        <div>
          <div class="flex items-center justify-between">
            <span
              class="text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold"
              :class="{
                'bg-purple-950 text-purple-300 border border-purple-800': canal.tipo === 'EVENTO',
                'bg-blue-950 text-blue-300 border border-blue-800': canal.tipo === 'DIGITAL',
                'bg-emerald-950 text-emerald-300 border border-emerald-800': canal.tipo === 'FISICO',
              }"
            >
              {{ canal.tipo }}
            </span>

            <span
              class="text-[10px] font-mono px-2 py-0.5 rounded"
              :class="canal.activo ? 'bg-emerald-950/60 text-emerald-400' : 'bg-stone-800 text-stone-500'"
            >
              {{ canal.activo ? 'Activo' : 'Inactivo' }}
            </span>
          </div>

          <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
            {{ canal.nombre }}
          </h3>
          <p class="text-xs text-stone-400 mt-1">
            {{ canal.descripcion }}
          </p>

          <div class="mt-4 bg-stone-950/70 p-3 rounded-lg border border-stone-800 space-y-2 text-xs font-mono">
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Comisión por Venta:</span>
              <span class="font-bold text-amber-300">{{ canal.comision_pct }}%</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Costo Fijo / Stand:</span>
              <span class="font-medium text-stone-200">{{ formatoCOP(canal.costo_fijo_mensual) }}</span>
            </div>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-end gap-2">
          <button
            :id="`btn-editar-canal-${canal.id}`"
            @click="abrirEditarCanal(canal)"
            class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
          >
            Editar
          </button>
          <button
            :id="`btn-eliminar-canal-${canal.id}`"
            @click="emit('solicitar-eliminar', { tipo: 'canal', id: canal.id, nombre: canal.nombre })"
            class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
            title="Eliminar Canal"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 2: CANAL DE VENTA -->
    <div
      v-if="modalCanal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionCanal ? 'Editar Canal Comercial' : 'Nuevo Canal de Venta' }}
          </h3>
          <button @click="modalCanal = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarCanal" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre Comercial:</label>
            <input
              id="input-canal-nombre"
              v-model="canalForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Feria NANA Pereira"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tipo:</label>
              <select
                id="input-canal-tipo"
                v-model="canalForm.tipo"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="DIGITAL">Digital (DM / Web)</option>
                <option value="FISICO">Físico (Showroom / Tienda)</option>
                <option value="EVENTO">Evento (Feria / Convención)</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Comisión (%):</label>
              <InputNumber
                v-model="canalForm.comision_pct"
                inputId="input-canal-comision"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.1"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Costo Fijo / Stand (COP):</label>
            <InputNumber
              v-model="canalForm.costo_fijo_mensual"
              inputId="input-canal-costo-fijo"
              mode="decimal"
              locale="es-CO"
              :min="0"
              :step="10000"
              :min-fraction-digits="0"
              :max-fraction-digits="2"
              suffix=" COP"
              class="w-full"
              inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Descripción:</label>
            <textarea
              id="input-canal-desc"
              v-model="canalForm.descripcion"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Notas y detalles del canal..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalCanal = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Canal
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
