<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import InputNumber from 'primevue/inputnumber'
import type { ParametrosRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'

const props = defineProps<{
  parametros: ParametrosRead | null
}>()

const emit = defineEmits<{
  (e: 'actualizado', val: ParametrosRead): void
}>()

const maestros = useMaestros()

const PARAMETROS_COSTEO_DEFAULT: ParametrosRead = {
  costo_minuto_costura: 280,
  costo_minuto_energia: 0,
  costo_hora_patronaje: 22000,
  margen_meta_global_pct: 65,
  desperdicio_textil_default_pct: 12,
  iva_regimen_pct: 0,
  distribucion_reinversion_pct: 40,
  reparto_margara_pct: 30,
  reparto_valqui_pct: 30,
} as ParametrosRead

const parametrosForm = ref<ParametrosRead>({ ...(props.parametros ?? PARAMETROS_COSTEO_DEFAULT) })
const guardandoParametros = ref(false)
const mensajeParametros = ref('')

watch(
  () => props.parametros,
  (val) => {
    if (val) Object.assign(parametrosForm.value, val)
  },
  { deep: true }
)

const sumaDistribucion = computed(() => {
  return (
    Number(parametrosForm.value.distribucion_reinversion_pct || 0) +
    Number(parametrosForm.value.reparto_margara_pct || 0) +
    Number(parametrosForm.value.reparto_valqui_pct || 0)
  )
})

async function guardarParametros() {
  if (sumaDistribucion.value !== 100) {
    alert(`La suma del reparto de utilidades debe ser exactamente 100% (actualmente suma ${sumaDistribucion.value}%).`)
    return
  }
  guardandoParametros.value = true
  try {
    const updated = await maestros.updateParametros(parametrosForm.value as unknown as Record<string, unknown>)
    Object.assign(parametrosForm.value, updated)
    emit('actualizado', updated as unknown as ParametrosRead)
    mensajeParametros.value = '✓ Parámetros maestros de costeo y márgenes guardados con éxito'
    setTimeout(() => { mensajeParametros.value = '' }, 4000)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al guardar parámetros'
    alert(msg)
  } finally {
    guardandoParametros.value = false
  }
}

function restaurarParametrosDefecto() {
  parametrosForm.value = { ...PARAMETROS_COSTEO_DEFAULT }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
      <div>
        <h2 class="text-lg font-serif font-bold text-stone-100">Tarifas Oficiales de Mano de Obra, Energía & Márgenes</h2>
        <p class="text-xs text-stone-400 font-mono">Bases de cálculo dinámico para el Cotizador Rápido y las Fichas de Producto.</p>
      </div>

      <button
        id="btn-restaurar-costeo"
        @click="restaurarParametrosDefecto"
        class="text-xs font-mono text-stone-400 hover:text-amber-300 px-3 py-1.5 rounded-lg border border-stone-800 hover:border-stone-700 bg-stone-900 transition-colors"
      >
        Restaurar Valores por Defecto
      </button>
    </div>

    <div class="bg-stone-900/60 border border-stone-800 rounded-xl p-6 space-y-6">
      <div v-if="mensajeParametros" class="p-3 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-300 font-mono text-xs flex items-center gap-2">
        {{ mensajeParametros }}
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Costo minuto costura -->
        <div class="space-y-2">
          <label for="param-minuto-costura" class="block text-xs font-mono text-stone-300">
            Valor Minuto de Confección (COP/min):
          </label>
          <div class="relative">
            <InputNumber
              v-model="parametrosForm.costo_minuto_costura"
              inputId="param-minuto-costura"
              mode="decimal"
              locale="es-CO"
              :min="0"
              :step="10"
              :min-fraction-digits="0"
              :max-fraction-digits="2"
              suffix=" COP"
              class="w-full"
              inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
            />
          </div>
          <p class="text-[11px] text-stone-400">Tarifa por minuto de armado, planchado y colocado de varillas.</p>
        </div>

        <!-- Costo minuto energía -->
        <div class="space-y-2">
          <label for="param-minuto-energia" class="block text-xs font-mono text-stone-300">
            Valor Minuto de Energía (COP/min):
          </label>
          <div class="relative">
            <InputNumber
              v-model="parametrosForm.costo_minuto_energia"
              inputId="param-minuto-energia"
              mode="decimal"
              locale="es-CO"
              :min="0"
              :step="10"
              :min-fraction-digits="0"
              :max-fraction-digits="2"
              suffix=" COP"
              class="w-full"
              inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
            />
          </div>
          <p class="text-[11px] text-stone-400">Tarifa por minuto de energía de maquinaria en costura.</p>
        </div>

        <!-- Costo hora patronaje -->
        <div class="space-y-2">
          <label for="param-hora-patronaje" class="block text-xs font-mono text-stone-300">
            Valor Hora Patronaje & Corte (COP/hora):
          </label>
          <div class="relative">
            <InputNumber
              v-model="parametrosForm.costo_hora_patronaje"
              inputId="param-hora-patronaje"
              mode="decimal"
              locale="es-CO"
              :min="0"
              :step="1000"
              :min-fraction-digits="0"
              :max-fraction-digits="2"
              suffix=" COP"
              class="w-full"
              inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
            />
          </div>
          <p class="text-[11px] text-stone-400">Hora de diseño, digitalización y corte manual de precisión.</p>
        </div>

        <!-- Margen global meta -->
        <div class="space-y-2">
          <label for="param-margen-meta" class="block text-xs font-mono text-stone-300">
            Margen Meta de Utilidad Sugerido (%):
          </label>
          <div class="relative">
            <InputNumber
              v-model="parametrosForm.margen_meta_global_pct"
              inputId="param-margen-meta"
              mode="decimal"
              locale="es-CO"
              :min="0"
              :max="100"
              :step="0.5"
              :min-fraction-digits="0"
              :max-fraction-digits="2"
              suffix=" %"
              class="w-full"
              inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
            />
          </div>
          <p class="text-[11px] text-stone-400">Margen por defecto aplicado en el Cotizador rápido.</p>
        </div>

        <!-- Desperdicio merma textil -->
        <div class="space-y-2">
          <label for="param-desperdicio" class="block text-xs font-mono text-stone-300">
            Factor de Merma / Desperdicio Textil (%):
          </label>
          <div class="relative">
            <InputNumber
              v-model="parametrosForm.desperdicio_textil_default_pct"
              inputId="param-desperdicio"
              mode="decimal"
              locale="es-CO"
              :min="0"
              :max="50"
              :step="0.5"
              :min-fraction-digits="0"
              :max-fraction-digits="2"
              suffix=" %"
              class="w-full"
              inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
            />
          </div>
          <p class="text-[11px] text-stone-400">Porcentaje de tela adicional estimado por mermas en tizado.</p>
        </div>

        <!-- Distribución 40/30/30 Editable -->
        <div class="space-y-2 md:col-span-2">
          <div class="flex items-center justify-between">
            <label class="block text-xs font-mono text-stone-300">
              Regla de Distribución de Utilidades Socias (Debe sumar 100%):
            </label>
            <span
              class="text-xs font-mono font-bold px-2 py-0.5 rounded"
              :class="sumaDistribucion === 100 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'"
            >
              Suma: {{ sumaDistribucion }}%
            </span>
          </div>

          <div class="grid grid-cols-3 gap-3 bg-stone-950 p-4 rounded-lg border border-stone-800 text-xs font-mono">
            <div>
              <label for="param-dist-taller" class="block text-stone-400 mb-1">Fondo Taller (%):</label>
              <InputNumber
                v-model="parametrosForm.distribucion_reinversion_pct"
                inputId="param-dist-taller"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.5"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                class="w-full"
                inputClass="w-full bg-stone-900 border border-stone-700 rounded-lg px-2.5 py-1.5 text-amber-300 font-bold focus:border-amber-400 focus:outline-none"
              />
            </div>

            <div>
              <label for="param-dist-margara" class="block text-stone-400 mb-1">Margara (%):</label>
              <InputNumber
                v-model="parametrosForm.reparto_margara_pct"
                inputId="param-dist-margara"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.5"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                class="w-full"
                inputClass="w-full bg-stone-900 border border-stone-700 rounded-lg px-2.5 py-1.5 text-stone-200 font-bold focus:border-amber-400 focus:outline-none"
              />
            </div>

            <div>
              <label for="param-dist-valqui" class="block text-stone-400 mb-1">Valqui (%):</label>
              <InputNumber
                v-model="parametrosForm.reparto_valqui_pct"
                inputId="param-dist-valqui"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.5"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                class="w-full"
                inputClass="w-full bg-stone-900 border border-stone-700 rounded-lg px-2.5 py-1.5 text-stone-200 font-bold focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>
          <p class="text-[11px] text-stone-400">Estatuto de reparto mensual de utilidades netas del taller. Al guardar, actualiza las socias (manda Maestros).</p>
        </div>
      </div>

      <div class="pt-4 border-t border-stone-800 flex justify-end">
        <button
          id="btn-guardar-parametros"
          @click="guardarParametros"
          :disabled="guardandoParametros || sumaDistribucion !== 100"
          class="bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-stone-950 font-mono text-xs font-bold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow"
        >
          <span>💾</span>
          <span>{{ guardandoParametros ? 'Guardando...' : 'Guardar Parámetros de Costeo' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
