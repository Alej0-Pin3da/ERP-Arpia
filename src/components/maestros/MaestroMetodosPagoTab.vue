<script setup lang="ts">
import { ref } from 'vue'
import InputNumber from 'primevue/inputnumber'
import type { MetodoRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'
import { showToast } from '@/utils/toast'

defineProps<{
  metodos: MetodoRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', payload: { tipo: string; id: number; nombre: string }): void
}>()

const maestros = useMaestros()

const modalPago = ref(false)
const modoEdicionPago = ref(false)
const pagoForm = ref<Partial<MetodoRead>>({
  nombre: '',
  tipo: 'TRANSFERENCIA',
  comision_pct: 0,
  tiempo_acreditacion: 'Inmediata',
  activo: true,
  datos_cuenta: '',
})

function sanitizeMetodoPayload(form: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const nombre = String(form.nombre ?? '').trim()
  if (nombre) out.nombre = nombre
  let codigo = String((form as any).codigo ?? '').trim()
  if (!codigo && nombre) {
    codigo = nombre.toUpperCase().replace(/\s+/g, '_').replace(/[^A-Z0-9_]/g, '').slice(0, 50) || 'METODO'
  }
  if (codigo) out.codigo = codigo
  const tipoRaw = String(form.tipo ?? '').trim().toUpperCase()
  if (['TRANSFERENCIA', 'BILLETERA_DIGITAL', 'EFECTIVO', 'PASARELA_DATAFONO'].includes(tipoRaw)) out.tipo = tipoRaw
  else out.tipo = 'TRANSFERENCIA'
  const com = form.comision_pct
  if (com !== '' && com !== null && com !== undefined) {
    const n = Number(com)
    if (!Number.isNaN(n)) out.comision_pct = Math.max(0, Math.min(100, n))
  }
  const tiempo = String(form.tiempo_acreditacion ?? '').trim()
  out.tiempo_acreditacion = tiempo || null
  out.activo = (form as any).activo !== false
  const datos = String((form as any).datos_cuenta ?? '').trim()
  out.datos_cuenta = datos || null
  const desc = String((form as any).descripcion ?? '').trim()
  out.descripcion = desc || null
  return out
}

function abrirNuevoPago() {
  modoEdicionPago.value = false
  pagoForm.value = {
    nombre: '',
    tipo: 'TRANSFERENCIA',
    comision_pct: 0,
    tiempo_acreditacion: 'Inmediata',
    activo: true,
    datos_cuenta: '',
  }
  modalPago.value = true
}

function abrirEditarPago(p: MetodoRead) {
  modoEdicionPago.value = true
  pagoForm.value = { ...p }
  modalPago.value = true
}

async function guardarPago() {
  if (!pagoForm.value.nombre) {
    showToast('warn', 'Campo requerido', 'Ingresá el nombre del método de pago.')
    return
  }
  const payload = sanitizeMetodoPayload(pagoForm.value as unknown as Record<string, unknown>)
  try {
    if (modoEdicionPago.value && pagoForm.value.id) {
      await maestros.updateMetodo(pagoForm.value.id, payload)
    } else {
      await maestros.createMetodo(payload)
    }
    emit('actualizado')
    showToast('success', 'Método guardado', `${pagoForm.value.nombre} guardado correctamente.`)
    modalPago.value = false
  } catch (e: unknown) {
    const msg = (e as any)?.response?.data?.detail ?? (e as Error)?.message ?? 'Error al guardar método de pago'
    const detail = Array.isArray(msg) ? msg.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : String(msg)
    showToast('error', 'Error 422', detail)
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
      <div>
        <h2 class="text-lg font-serif font-bold text-stone-100">Medios de Pago & Pasarelas</h2>
        <p class="text-xs text-stone-400 font-mono">Configuración de cuentas bancarias, pasarelas Bold/Wompi y comisiones financieras aplicadas.</p>
      </div>

      <button
        id="btn-nuevo-pago"
        @click="abrirNuevoPago"
        class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
      >
        <span>+</span> Nuevo Método de Pago
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="pago in metodos"
        :key="pago.id"
        :id="`card-pago-${pago.id}`"
        class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
      >
        <div>
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-amber-300 border border-stone-700/60">
              {{ (pago.tipo ?? '').replace('_', ' ') }}
            </span>
            <span
              class="text-[10px] font-mono px-2 py-0.5 rounded"
              :class="pago.activo ? 'bg-emerald-950/60 text-emerald-400' : 'bg-stone-800 text-stone-500'"
            >
              {{ pago.activo ? 'Habilitado' : 'Deshabilitado' }}
            </span>
          </div>

          <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
            {{ pago.nombre }}
          </h3>

          <div class="mt-3 bg-stone-950/70 p-3 rounded-lg border border-stone-800 space-y-2 text-xs font-mono">
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Tasa Comisión:</span>
              <span class="font-bold text-amber-300">{{ pago.comision_pct }}%</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Acreditación:</span>
              <span class="font-medium text-stone-200">{{ pago.tiempo_acreditacion }}</span>
            </div>
            <div v-if="pago.datos_cuenta" class="pt-1 border-t border-stone-800/80">
              <div class="text-stone-500 text-[11px]">Detalle / Cuenta:</div>
              <div class="text-stone-300 text-[11px] break-words">{{ pago.datos_cuenta }}</div>
            </div>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-end gap-2">
          <button
            :id="`btn-editar-pago-${pago.id}`"
            @click="abrirEditarPago(pago)"
            class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
          >
            Editar
          </button>
          <button
            :id="`btn-eliminar-pago-${pago.id}`"
            @click="emit('solicitar-eliminar', { tipo: 'metodo', id: pago.id, nombre: pago.nombre })"
            class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
            title="Eliminar Método"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 3: MÉTODO DE PAGO (CRUD) -->
    <div
      v-if="modalPago"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionPago ? 'Editar Método de Pago' : 'Nuevo Método de Pago' }}
          </h3>
          <button @click="modalPago = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarPago" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre Comercial:</label>
            <input
              id="input-pago-nombre"
              v-model="pagoForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Transferencia Bancolombia"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tipo:</label>
              <select
                id="input-pago-tipo"
                v-model="pagoForm.tipo"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="TRANSFERENCIA">Transferencia Bancaria</option>
                <option value="BILLETERA_DIGITAL">Billetera Móvil (Nequi/Davi)</option>
                <option value="EFECTIVO">Efectivo / Caja</option>
                <option value="PASARELA_DATAFONO">Pasarela / Datáfono</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Comisión (%):</label>
              <InputNumber
                v-model="pagoForm.comision_pct"
                inputId="input-pago-comision"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.01"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Tiempo de Acreditación:</label>
            <input
              id="input-pago-tiempo"
              v-model="pagoForm.tiempo_acreditacion"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Inmediata / 24 horas"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Detalle de Cuenta / Llave:</label>
            <input
              id="input-pago-cuenta"
              v-model="pagoForm.datos_cuenta"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Número de cuenta, teléfono o link"
            />
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalPago = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Método
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
