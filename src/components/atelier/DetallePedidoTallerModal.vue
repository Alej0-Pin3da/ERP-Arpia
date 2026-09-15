<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { showToast } from '@/utils/toast'
import {
  FASES_PRODUCCION,
  FASES_TIEMPO,
  createTiempoPedido,
  extractApiDetail,
  listTiemposPedido,
  siguienteFase,
  updatePedidoProduccion,
  updateTiempoPedido,
} from '@/services/api/pedidos-produccion'
import type { TiempoFaseRead } from '@/services/api/pedidos-produccion'

/** Minimal pedido shape this modal reads (REAL display object from the caller). */
export interface PedidoTallerDetalle {
  id: number
  codigo: string
  cliente_nombre: string
  prenda_nombre: string
  estado: string
  // Workshop phase + lot data (backend migración 0030; null-safe for legacy rows).
  fase?: string | null
  cantidad?: number | null
  cantidad_producida?: number | null
  costo_unitario_snapshot?: number | string | null
  precio_venta?: number
  // Real labor/energy cost derived at read time from TiempoFase rows
  // (null/undefined while no tiempos are logged — "no data").
  mano_obra_real?: number | string | null
  energia_real?: number | string | null
}

const props = defineProps<{
  visible: boolean
  pedido: PedidoTallerDetalle | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'fase-avanzada', fase: string): void
  (e: 'tiempos-actualizados'): void
}>()

// Tiempos reales por fase (backend GET/POST/PATCH
// /pedidos-produccion/{id}/tiempos, migración 0031): un renglón por
// (pedido, fase) con operaria + minutos; costos derivados a lectura.
const tiempos = ref<TiempoFaseRead[]>([])
const totalMinutos = ref<number | string>(0)
const totalManoObra = ref<number | string>(0)
const totalEnergia = ref<number | string>(0)
const cargandoTiempos = ref(false)
const errorTiempos = ref<string | null>(null)

// Alta: fase (corte|costura|acabados|calidad) + operaria + minutos + fecha (hoy).
const hoyISO = () => new Date().toISOString().split('T')[0]
const faseNueva = ref<string>(FASES_TIEMPO[0])
const operariaNueva = ref('')
const minutosNuevos = ref<number | null>(null)
const fechaNueva = ref<string>(hoyISO())
const guardandoTiempo = ref(false)

// Edición inline (PATCH solo corrige operaria/minutos_reales).
const editandoId = ref<number | null>(null)
const editOperaria = ref('')
const editMinutos = ref<number | null>(null)
const actualizandoTiempo = ref(false)

const pruebasCalce = ref<Array<{ id: number; fecha: string; tipo: string; estado: string; notas: string }>>([])

const anticipoPagado = ref<boolean | null>(null)

const totalHorasTaller = computed(() =>
  tiempos.value.length ? `${Number(totalMinutos.value).toLocaleString('es-CO')} min` : '—',
)

// Costos reales del pedido (el padre los trae en el read; null = sin tiempos).
const tieneCostosReales = computed(
  () =>
    props.pedido?.mano_obra_real !== null &&
    props.pedido?.mano_obra_real !== undefined,
)
const tieneEnergiaReal = computed(
  () =>
    props.pedido?.energia_real !== null &&
    props.pedido?.energia_real !== undefined,
)

// Fase actual: prop del backend, con override local tras un avance exitoso
// (el objeto del padre es un snapshot y puede tardar en recargarse).
const faseLocal = ref<string | null>(null)
const errorAvance = ref<string | null>(null)
const avanzando = ref(false)

watch(
  () => props.pedido,
  () => {
    faseLocal.value = null
    errorAvance.value = null
  },
)

watch(
  () => [props.pedido?.id, props.visible] as const,
  ([id, visible]) => {
    if (id && visible) void cargarTiempos()
  },
  { immediate: true },
)

function resetFormaTiempo() {
  const pendientes = FASES_TIEMPO.filter((f) => !tiempos.value.some((t) => t.fase === f))
  faseNueva.value = pendientes[0] ?? FASES_TIEMPO[0]
  operariaNueva.value = ''
  minutosNuevos.value = null
  fechaNueva.value = hoyISO()
  editandoId.value = null
}

async function cargarTiempos() {
  if (!props.pedido) return
  cargandoTiempos.value = true
  errorTiempos.value = null
  try {
    const res = await listTiemposPedido(props.pedido.id)
    tiempos.value = res.items
    totalMinutos.value = res.total_minutos
    totalManoObra.value = res.total_mano_obra
    totalEnergia.value = res.total_energia
    resetFormaTiempo()
  } catch (e: unknown) {
    errorTiempos.value = extractApiDetail(e)
  } finally {
    cargandoTiempos.value = false
  }
}

async function guardarTiempo() {
  if (!props.pedido || guardandoTiempo.value) return
  if (!operariaNueva.value.trim() || minutosNuevos.value === null) {
    showToast('warn', 'Faltan datos', 'Indicá la operaria y los minutos reales antes de guardar.')
    return
  }
  guardandoTiempo.value = true
  errorTiempos.value = null
  try {
    await createTiempoPedido(props.pedido.id, {
      fase: faseNueva.value,
      operaria: operariaNueva.value.trim(),
      minutos_reales: minutosNuevos.value,
      fecha: fechaNueva.value || undefined,
    })
    showToast('success', 'Tiempo registrado', `Fase ${faseNueva.value.toUpperCase()} cargada en la orden ${props.pedido.codigo}.`)
    await cargarTiempos()
    emit('tiempos-actualizados')
  } catch (e: unknown) {
    // 400 fuera-de-orden / 409 duplicado / 422 fase o minutos inválidos, verbatim.
    const detail = extractApiDetail(e)
    errorTiempos.value = detail
    showToast('error', 'No se pudo registrar', detail)
  } finally {
    guardandoTiempo.value = false
  }
}

function iniciarEdicion(t: TiempoFaseRead) {
  editandoId.value = t.id
  editOperaria.value = t.operaria
  editMinutos.value = Number(t.minutos_reales)
  errorTiempos.value = null
}

function cancelarEdicion() {
  editandoId.value = null
}

async function guardarEdicion(t: TiempoFaseRead) {
  if (!props.pedido || actualizandoTiempo.value) return
  if (!editOperaria.value.trim() || editMinutos.value === null) {
    showToast('warn', 'Faltan datos', 'Indicá la operaria y los minutos reales antes de guardar.')
    return
  }
  actualizandoTiempo.value = true
  errorTiempos.value = null
  try {
    await updateTiempoPedido(props.pedido.id, t.id, {
      operaria: editOperaria.value.trim(),
      minutos_reales: editMinutos.value,
    })
    showToast('success', 'Tiempo corregido', `Fase ${t.fase.toUpperCase()} actualizada en la orden ${props.pedido.codigo}.`)
    editandoId.value = null
    await cargarTiempos()
    emit('tiempos-actualizados')
  } catch (e: unknown) {
    const detail = extractApiDetail(e)
    errorTiempos.value = detail
    showToast('error', 'No se pudo corregir', detail)
  } finally {
    actualizandoTiempo.value = false
  }
}

const faseActual = computed(() => faseLocal.value ?? props.pedido?.fase ?? null)
const faseSiguiente = computed(() => siguienteFase(faseActual.value))
const tieneCostoSnapshot = computed(
  () =>
    props.pedido?.costo_unitario_snapshot !== null &&
    props.pedido?.costo_unitario_snapshot !== undefined,
)

async function avanzarFase() {
  if (!props.pedido || avanzando.value) return
  const next = faseSiguiente.value
  if (!next) return
  avanzando.value = true
  errorAvance.value = null
  try {
    const updated = await updatePedidoProduccion(props.pedido.id, { fase: next })
    faseLocal.value = updated.fase
    emit('fase-avanzada', updated.fase)
    showToast('success', 'Fase actualizada', `Orden ${props.pedido.codigo} avanzada a ${next.toUpperCase()}.`)
  } catch (e: unknown) {
    // 400/422/409 del backend, verbatim (incluye el detalle por-insumo del 409).
    const detail = extractApiDetail(e)
    errorAvance.value = detail
    showToast('error', 'No se pudo avanzar', detail)
  } finally {
    avanzando.value = false
  }
}

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function generarReciboAnticipo() {
  showToast(
    'success',
    'Recibo de Caja Generado',
    `Comprobante de anticipo por ${formatCOP((props.pedido?.precio_venta || 0) * 0.5)} listo para enviar a la clienta.`
  )
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    modal
    :header="`Ficha de Taller & Tiempos: ${props.pedido?.codigo || 'Pedido'} - ${props.pedido?.prenda_nombre}`"
    :style="{ width: '840px', maxWidth: '95vw' }"
    class="p-dialog-arpia"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="space-y-6 pt-1">
      <!-- Order Summary Card -->
      <div class="rounded-2xl border border-stone-800 bg-stone-950/70 p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-stone-100">{{ props.pedido?.cliente_nombre }}</span>
            <span class="text-xs font-mono text-amber-400 font-bold">({{ props.pedido?.codigo }})</span>
          </div>
          <div class="text-xs text-stone-400 font-mono">
            Prenda: <strong class="text-stone-200">{{ props.pedido?.prenda_nombre }}</strong> · Estado: <span class="text-amber-300 font-bold">{{ props.pedido?.estado }}</span>
          </div>
        </div>

        <div class="flex items-center gap-4 text-xs font-mono">
          <div class="bg-stone-900 border border-stone-800 p-2 rounded-lg text-center">
            <span class="text-[10px] text-stone-400 block">Horas Acumuladas</span>
            <span class="text-amber-300 font-bold text-sm">{{ totalHorasTaller }}</span>
          </div>
          <div class="bg-stone-900 border border-stone-800 p-2 rounded-lg text-center">
            <span class="text-[10px] text-stone-400 block">Precio Acordado</span>
            <span class="text-emerald-400 font-bold text-sm">{{ formatCOP(props.pedido?.precio_venta || 0) }}</span>
          </div>
          <div v-if="tieneCostosReales" class="bg-stone-900 border border-stone-800 p-2 rounded-lg text-center">
            <span class="text-[10px] text-stone-400 block">Mano de obra real</span>
            <span class="text-sky-300 font-bold text-sm">{{ formatCOP(Number(props.pedido?.mano_obra_real)) }}</span>
          </div>
          <div v-if="tieneEnergiaReal" class="bg-stone-900 border border-stone-800 p-2 rounded-lg text-center">
            <span class="text-[10px] text-stone-400 block">Energía real</span>
            <span class="text-sky-300 font-bold text-sm">{{ formatCOP(Number(props.pedido?.energia_real)) }}</span>
          </div>
        </div>
      </div>

      <!-- Anticipo: solo con datos reales de venta/anticipo. Sin endpoint, se oculta con nota. -->
      <div v-if="anticipoPagado === null" class="rounded-xl border border-stone-800 bg-stone-900/60 p-4 text-xs text-stone-400 font-mono">
        Sin registro — pendiente: el control de anticipos requiere datos reales de venta/anticipo.
      </div>

      <!-- Fase & lote (datos REALES del backend, migración 0030) -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Fase de confección & avance de lote
        </div>
        <div class="rounded-xl border border-stone-800 bg-stone-950/60 p-4 space-y-3">
          <!-- 5-phase stepper -->
          <div class="flex items-center gap-1">
            <template v-for="(f, i) in FASES_PRODUCCION" :key="f">
              <div class="flex-1 text-center">
                <div
                  class="mx-auto w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border"
                  :class="faseActual && FASES_PRODUCCION.indexOf(faseActual) >= i
                    ? 'bg-amber-500 text-stone-950 border-amber-500'
                    : 'bg-stone-900 text-stone-500 border-stone-700'"
                >
                  {{ i + 1 }}
                </div>
                <div
                  class="text-[9px] font-mono uppercase mt-1"
                  :class="faseActual === f ? 'text-amber-300 font-bold' : 'text-stone-500'"
                >
                  {{ f }}
                </div>
              </div>
              <div v-if="i < FASES_PRODUCCION.length - 1" class="h-px flex-1 bg-stone-800 -mt-4" />
            </template>
          </div>

          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
            <div class="text-stone-400">
              Fase actual: <strong class="text-amber-300">{{ (faseActual || '—').toUpperCase() }}</strong>
              <span class="text-stone-500">·</span>
              Lote: <strong class="text-stone-200">{{ props.pedido?.cantidad_producida ?? 0 }}/{{ props.pedido?.cantidad ?? '—' }} uds</strong>
              <template v-if="tieneCostoSnapshot">
                <span class="text-stone-500">·</span>
                Costo unit.: <strong class="text-emerald-400">{{ formatCOP(Number(props.pedido?.costo_unitario_snapshot)) }}</strong>
              </template>
            </div>
            <Button
              v-if="faseSiguiente"
              label="Avanzar fase"
              icon="pi pi-arrow-right"
              size="small"
              class="p-button-warning text-xs font-semibold"
              :loading="avanzando"
              :disabled="avanzando"
              @click="avanzarFase"
            />
            <span v-else class="text-[11px] text-stone-500">Lote en fase final.</span>
          </div>

          <!-- Backend error verbatim (400 salto/retroceso, 422 fase inválida, 409 faltante con detalle por-insumo) -->
          <div v-if="errorAvance" class="rounded-lg border border-red-500/40 bg-red-950/40 p-3 text-[11px] text-red-300 font-mono whitespace-pre-wrap">
            {{ errorAvance }}
          </div>
        </div>
      </div>

      <!-- Workshop Phases & Timing Log (REAL: GET/POST/PATCH .../tiempos) -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Tiempos Reales por Fase de Modistería
        </div>
        <div class="border border-stone-800 rounded-xl bg-stone-950/60 p-4 space-y-3">
          <div v-if="cargandoTiempos" class="p-4 text-center text-xs text-stone-400 font-mono">
            Cargando tiempos…
          </div>

          <div v-else-if="!tiempos.length" class="p-4 text-center text-xs text-stone-400 font-mono">
            Sin registro de tiempos por fase — pendiente.
          </div>

          <div v-else class="space-y-2">
            <div
              v-for="t in tiempos"
              :key="t.id"
              class="rounded-lg border border-stone-800 bg-stone-900/60 p-3 text-xs font-mono"
            >
              <template v-if="editandoId !== t.id">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <span class="font-bold uppercase text-amber-300">{{ t.fase }}</span>
                  <span class="text-stone-400">{{ t.fecha }}</span>
                </div>
                <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-stone-300">
                  <span>Operaria: <strong class="text-stone-100">{{ t.operaria }}</strong></span>
                  <span>Minutos: <strong class="text-stone-100">{{ Number(t.minutos_reales).toLocaleString('es-CO') }}</strong></span>
                </div>
                <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-stone-400">
                  <span>Mano de obra: <strong class="text-sky-300">{{ formatCOP(Number(t.costo_mano_obra ?? 0)) }}</strong></span>
                  <span>Energía: <strong class="text-sky-300">{{ formatCOP(Number(t.costo_energia ?? 0)) }}</strong></span>
                </div>
                <div class="mt-2 flex justify-end">
                  <button
                    type="button"
                    class="text-[11px] text-amber-400 hover:text-amber-300 font-bold transition"
                    @click="iniciarEdicion(t)"
                  >
                    Corregir
                  </button>
                </div>
              </template>
              <template v-else>
                <div class="font-bold uppercase text-amber-300">{{ t.fase }} · corrigiendo</div>
                <div class="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <label class="block">
                    <span class="text-[10px] text-stone-400 uppercase">Operaria</span>
                    <input
                      v-model="editOperaria"
                      type="text"
                      class="mt-1 w-full rounded-lg border border-stone-700 bg-stone-950 px-2 py-1.5 text-xs text-stone-100"
                    />
                  </label>
                  <label class="block">
                    <span class="text-[10px] text-stone-400 uppercase">Minutos reales</span>
                    <input
                      v-model.number="editMinutos"
                      type="number"
                      min="0"
                      step="0.01"
                      class="mt-1 w-full rounded-lg border border-stone-700 bg-stone-950 px-2 py-1.5 text-xs text-stone-100"
                    />
                  </label>
                </div>
                <div class="mt-2 flex justify-end gap-2">
                  <Button
                    label="Cancelar"
                    size="small"
                    severity="secondary"
                    outlined
                    class="text-xs"
                    @click="cancelarEdicion"
                  />
                  <Button
                    label="Guardar"
                    icon="pi pi-check"
                    size="small"
                    class="p-button-warning text-xs font-semibold"
                    :loading="actualizandoTiempo"
                    :disabled="actualizandoTiempo"
                    @click="guardarEdicion(t)"
                  />
                </div>
              </template>
            </div>

            <!-- Totals footer -->
            <div class="rounded-lg border border-amber-500/30 bg-amber-950/30 p-3 text-xs font-mono flex flex-wrap gap-x-5 gap-y-1 text-stone-200">
              <span>Total: <strong class="text-amber-300">{{ Number(totalMinutos).toLocaleString('es-CO') }} min</strong></span>
              <span>Mano de obra: <strong class="text-amber-300">{{ formatCOP(Number(totalManoObra)) }}</strong></span>
              <span>Energía: <strong class="text-amber-300">{{ formatCOP(Number(totalEnergia)) }}</strong></span>
            </div>
          </div>

          <!-- Add form -->
          <div class="rounded-lg border border-stone-800 bg-stone-900/60 p-3">
            <div class="text-[11px] font-mono font-bold text-stone-300 uppercase mb-2">
              Registrar tiempo
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              <label class="block">
                <span class="text-[10px] text-stone-400 uppercase font-mono">Fase</span>
                <select
                  v-model="faseNueva"
                  class="mt-1 w-full rounded-lg border border-stone-700 bg-stone-950 px-2 py-1.5 text-xs text-stone-100 font-mono uppercase"
                >
                  <option v-for="f in FASES_TIEMPO" :key="f" :value="f">{{ f }}</option>
                </select>
              </label>
              <label class="block">
                <span class="text-[10px] text-stone-400 uppercase font-mono">Operaria</span>
                <input
                  v-model="operariaNueva"
                  type="text"
                  placeholder="Nombre de la operaria"
                  class="mt-1 w-full rounded-lg border border-stone-700 bg-stone-950 px-2 py-1.5 text-xs text-stone-100"
                />
              </label>
              <label class="block">
                <span class="text-[10px] text-stone-400 uppercase font-mono">Minutos</span>
                <input
                  v-model.number="minutosNuevos"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0"
                  class="mt-1 w-full rounded-lg border border-stone-700 bg-stone-950 px-2 py-1.5 text-xs text-stone-100"
                />
              </label>
              <label class="block">
                <span class="text-[10px] text-stone-400 uppercase font-mono">Fecha</span>
                <input
                  v-model="fechaNueva"
                  type="date"
                  class="mt-1 w-full rounded-lg border border-stone-700 bg-stone-950 px-2 py-1.5 text-xs text-stone-100"
                />
              </label>
            </div>
            <div class="mt-2 flex justify-end">
              <Button
                label="Guardar tiempo"
                icon="pi pi-plus"
                size="small"
                class="p-button-warning text-xs font-semibold"
                :loading="guardandoTiempo"
                :disabled="guardandoTiempo"
                @click="guardarTiempo"
              />
            </div>
          </div>

          <!-- Backend error verbatim (400 fuera-de-orden, 409 duplicado, 422 fase/minutos) -->
          <div v-if="errorTiempos" class="rounded-lg border border-red-500/40 bg-red-950/40 p-3 text-[11px] text-red-300 font-mono whitespace-pre-wrap">
            {{ errorTiempos }}
          </div>
        </div>
      </div>

      <!-- Fitting Sessions (Pruebas de Calce) -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Historial de Pruebas de Calce en Atelier
        </div>
        <div class="border border-stone-800 rounded-xl bg-stone-900/40 p-6 text-center text-xs text-stone-400 font-mono">
          Sin pruebas de calce registradas — pendiente.
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end w-full pt-3 border-t border-stone-800">
        <Button
          label="Cerrar Ficha"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="emit('update:visible', false)"
        />
      </div>
    </template>
  </Dialog>
</template>
