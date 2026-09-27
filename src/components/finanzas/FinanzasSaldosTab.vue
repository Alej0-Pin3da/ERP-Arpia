<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import { showToast } from '@/utils/toast'
import { getApiErrorDetail } from '@/utils/api-error'
import { listSaldos, listReglas, createRegla, updateRegla, type ReglaRead, type SaldoRead } from '@/services/api/reparto'

const saldos = ref<SaldoRead[]>([])
const reglas = ref<ReglaRead[]>([])
const cargando = ref(false)
const nuevaCuenta = ref('')
const nuevoPct = ref<number>(0)

async function cargar() {
  cargando.value = true
  try {
    const [s, r] = await Promise.all([listSaldos(), listReglas()])
    saldos.value = s ?? []
    reglas.value = r ?? []
  } catch {
    // keep previous state on error
  } finally {
    cargando.value = false
  }
}

onMounted(() => { void cargar() })

function formatCOP(val: number | string): string {
  return `$${Math.round(Number(val ?? 0)).toLocaleString('es-CO')}`
}

async function crearRegla() {
  if (!nuevaCuenta.value.trim()) {
    showToast('warn', 'Sin cuenta', 'Poné nombre a la cuenta destino.')
    return
  }
  try {
    await createRegla({ cuenta_destino: nuevaCuenta.value.trim(), porcentaje: nuevoPct.value })
    showToast('success', 'Regla creada', `${nuevaCuenta.value.trim()} reparte desde la próxima venta.`)
    nuevaCuenta.value = ''
    nuevoPct.value = 0
    await cargar()
  } catch (e: unknown) {
    showToast('error', 'No se pudo crear', getApiErrorDetail(e, '¿Cuenta duplicada?'))
  }
}

async function toggleRegla(r: ReglaRead) {
  try {
    await updateRegla(r.id, { activo: !r.activo })
    await cargar()
  } catch (e: unknown) {
    showToast('error', 'No se pudo cambiar', getApiErrorDetail(e, 'Revisá la conexión.'))
  }
}
</script>

<template>
  <div class="space-y-4">
    <p class="text-[11px] text-stone-500 m-0">
      Saldos en vivo por cada venta confirmada (informativos — el cierre oficial sigue siendo la liquidación).
    </p>

    <div v-if="cargando" class="text-xs text-stone-500">Cargando saldos...</div>
    <div v-else-if="!saldos.length" class="text-xs text-stone-500 rounded-xl border border-stone-800 bg-stone-950/60 p-4">
      Todavía no hay movimientos: se acreditan solos con cada venta confirmada.
    </div>
    <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div v-for="s in saldos" :key="s.cuenta" class="rounded-2xl border border-stone-800 bg-stone-900/80 p-4">
        <div class="text-xs text-stone-400 truncate">{{ s.cuenta }}</div>
        <div class="font-mono font-extrabold text-lg text-emerald-300">{{ formatCOP(s.saldo) }}</div>
      </div>
    </div>

    <div class="rounded-2xl border border-stone-800 bg-stone-900/80 p-4 space-y-3">
      <div class="text-xs font-bold uppercase tracking-wider text-amber-400">Reglas de reparto (%)</div>
      <div v-for="r in reglas" :key="r.id" class="flex items-center justify-between gap-2 text-xs">
        <span class="text-stone-200 truncate">{{ r.cuenta_destino }}</span>
        <span class="flex items-center gap-2">
          <span class="font-mono text-stone-300">{{ Number(r.porcentaje) }}%</span>
          <button
            type="button"
            class="px-2 py-1 rounded-lg text-[11px] font-bold"
            :class="r.activo ? 'bg-emerald-600/20 border border-emerald-500/30 text-emerald-300' : 'bg-stone-800 text-stone-400'"
            @click="toggleRegla(r)"
          >
            {{ r.activo ? 'activa' : 'pausada' }}
          </button>
        </span>
      </div>
      <div class="flex items-end gap-2 pt-1">
        <div class="flex-1">
          <InputText v-model="nuevaCuenta" placeholder="Nueva cuenta destino" class="w-full text-xs" />
        </div>
        <div class="w-24">
          <InputNumber v-model="nuevoPct" :min="0" suffix="%" placeholder="%" class="w-full font-mono text-xs" />
        </div>
        <Button label="Crear regla" size="small" class="text-xs" @click="crearRegla" />
      </div>
    </div>
  </div>
</template>
