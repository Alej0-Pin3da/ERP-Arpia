<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-empty */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import { useInsumos } from '@/composables/useInsumos'
import { useProduccion } from '@/composables/useProduccion'
import { useVentas } from '@/composables/useVentas'
import { useAnaliticos } from '@/composables/useAnaliticos'
import { useSocios } from '@/composables/useSocios'
import { useFinanzas } from '@/composables/useFinanzas'
import NuevoPedidoModal from '@/components/atelier/NuevoPedidoModal.vue'
import SugerirOrdenModal from '@/components/atelier/SugerirOrdenModal.vue'

const router = useRouter()
const insumosApi = useInsumos()
const produccionApi = useProduccion()
const ventasApi = useVentas()
const analiticosApi = useAnaliticos()
const sociosApi = useSocios()
const finanzasApi = useFinanzas()
const insumos = ref<any[]>([])
const pedidos = ref<any[]>([])
const ventas = ref<any[]>([])
const socias = ref<any[]>([])
const liquidaciones = ref<any[]>([])
// Resumen del backend con fallback al cómputo local si falla.
const resumen = ref<any | null>(null)
async function cargarDashboard() {
  try {
    const [ir, pr, vr] = await Promise.all([
      insumosApi.list({ limit: 100 }),
      produccionApi.list({ limit: 100 }),
      ventasApi.list({ limit: 100 }),
    ])
    insumos.value = (ir as any).items ?? []
    pedidos.value = (pr as any).items ?? []
    ventas.value = (vr as any).items ?? []
  } catch {}
  try {
    resumen.value = await analiticosApi.getResumen()
  } catch { resumen.value = null }
  // REAL-only: reparto desde GET /socios + /liquidaciones (como FinanzasView).
  try {
    const [sr, lr] = await Promise.all([
      sociosApi.list({ limit: 100, offset: 0 }),
      finanzasApi.listLiquidaciones({ limit: 100, offset: 0 }),
    ])
    socias.value = (sr as any).items ?? []
    liquidaciones.value = (lr as any).items ?? []
  } catch { socias.value = []; liquidaciones.value = [] }
}
onMounted(() => { void cargarDashboard() })

const insumosCriticos = computed(() => (insumos.value as any[]).filter((i: any) => Number(i.stock_actual ?? i.stock ?? 0) <= Number(i.stock_minimo ?? 0)))
// En REAL la API (PedidoProduccionRead) no trae codigo/cliente_nombre/
// prenda_nombre ni montos; se normaliza como en ProduccionView para no
// renderizar celdas vacías ni $NaN (Numeric serializa como string).
const pedidosTabla = computed(() => {
  return (pedidos.value as any[]).map((p: any) => {
    const rawEstado = String(p.estado ?? '')
    const fase = String(p.fase || 'corte')
    return {
      ...p,
      codigo: `ORD-${p.id}`,
      cliente_nombre: p.cliente_nombre || p.nombre_variante || p.nombre_producto || '—',
      prenda_nombre: p.nombre_producto || (p.producto_id ? `Producto #${p.producto_id}` : '—'),
      // La fase real viene del campo fase; el estado solo distingue terminales.
      estado: rawEstado === 'cancelado' ? 'CANCELADO' : rawEstado === 'completado' ? 'LISTO' : fase.toUpperCase(),
      precio_venta: Number(p.precio_venta ?? 0),
      utilidad_neta: Number(p.utilidad_neta ?? 0),
      margen_pct: Number(p.margen_pct ?? 0),
    }
  })
})

const ventasMensuales = ref<any[]>([])
// En REAL se prefiere el agregado del backend (snapshot, excluye anuladas);
// si el endpoint falla, se usa el cómputo local sobre ventas.
const totalVentas = computed(() => {
  if (resumen.value != null) return Number(resumen.value.ventas_total ?? 0)
  return (ventas.value as any[]).reduce((acc: number, v: any) => acc + Number(v.total_venta ?? v.total ?? 0), 0)
})
const totalUtilidad = computed(() => {
  if (resumen.value != null) return Number(resumen.value.margen_total ?? 0)
  return (ventas.value as any[]).reduce((acc: number, v: any) => acc + Number(v.ganancia_neta ?? v.utilidad_neta ?? 0), 0)
})
const rentabilidad = computed(()=> (() => { const v = ventas.value as any[]; if (!v.length) return 0; const total = v.reduce((a,c)=>a+Number(c.total_venta??0),0); const gan = v.reduce((a,c)=>a+Number(c.ganancia_neta??0),0); return total ? Math.round((gan/total)*100) : 0 })())
const pedidosActivos = computed(() => pedidos.value.filter((p: any) => p.estado !== 'ENTREGADO' && p.estado !== 'entregado').length)
const pipelineCounts = computed(() => {
  const counts: Record<string, number> = { COTIZADO:0, RESERVADO:0, CORTE:0, COSTURA:0, ACABADOS:0, CALIDAD:0, LISTO:0, ENTREGADO:0 }
  ;(pedidos.value as any[]).forEach((p: any) => { const k = String(p.estado||'').toUpperCase(); if (k in counts) counts[k]++ })
  return counts
})
// REAL-only: reparto desde GET /socios + /liquidaciones (como FinanzasView).
// Se oculta la sección cuando no hay datos; nunca se fabrica un 40/30/30.
const sociasRepartoDashboard = computed(() =>
  (socias.value as any[]).filter((s: any) => !s.es_fondo_taller && s.activo !== false).slice(0, 2),
)
const tieneRepartoReal = computed(() => sociasRepartoDashboard.value.length > 0 && liquidaciones.value.length > 0)
function totalRepartidoSociaDashboard(sociaId: number | undefined): number {
  if (sociaId == null) return 0
  return (liquidaciones.value as any[]).reduce((a: number, l: any) => {
    const item = (l.distribucion as any[] ?? []).find((d: any) => d.socia_id === sociaId)
    return a + (item ? Number(item.monto_neto ?? item.monto_neto_pagar ?? 0) : 0)
  }, 0)
}
const distribucion = computed(() => {
  const total = totalUtilidad.value
  const fondo = (liquidaciones.value as any[]).reduce((a: number, l: any) => a + Number(l.fondo_reinversion_monto ?? 0), 0)
  const s0 = sociasRepartoDashboard.value[0] as any
  const s1 = sociasRepartoDashboard.value[1] as any
  return {
    total,
    fondo,
    socia0: { nombre: s0 ? String(s0.nombre ?? '—') : '—', porcentaje: Number(s0?.porcentaje ?? s0?.porcentaje_participacion ?? 0), monto: totalRepartidoSociaDashboard(s0?.id) },
    socia1: { nombre: s1 ? String(s1.nombre ?? '—') : '—', porcentaje: Number(s1?.porcentaje ?? s1?.porcentaje_participacion ?? 0), monto: totalRepartidoSociaDashboard(s1?.id) },
  }
})


const showNuevoPedidoModal = ref(false)
const showSugerirModal = ref(false)

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function getEstadoBadgeClass(estado: string) {
  switch (estado) {
    case 'ENTREGADO':
      return 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
    case 'COSTURA':
      return 'bg-amber-950/60 text-amber-300 border border-amber-500/30'
    case 'CORTE':
      return 'bg-blue-950/60 text-blue-300 border border-blue-500/30'
    case 'LISTO':
      return 'bg-purple-950/60 text-purple-300 border border-purple-500/30'
    default:
      return 'bg-stone-800 text-stone-300 border border-stone-700'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Top Banner: Panel General de Operaciones -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl relative overflow-hidden">
      <div class="absolute -right-12 -top-12 w-48 h-48 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
        <div class="space-y-1.5">
          <div class="flex items-center gap-2.5 flex-wrap">
            <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
              Panel General de Operaciones
            </h1>
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
              Operación Activa
            </span>
          </div>
          <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
            Resumen de rentabilidad, balance de insumos textiles y flujo de confección en tiempo real.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            label="Cotizador Rápido"
            icon="pi pi-calculator"
            size="small"
            severity="secondary"
            outlined
            class="text-xs font-semibold"
            @click="router.push('/cotizador')"
          />
          <Button
            label="Nuevo Pedido"
            icon="pi pi-plus"
            size="small"
            class="p-button-warning text-xs font-semibold"
            @click="showNuevoPedidoModal = true"
          />
        </div>
      </div>
    </div>

    <!-- 4 Main KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 1. Rentabilidad Mes -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-amber-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Rentabilidad Mes</span>
            <!-- Sin delta: no hay endpoint de comparativa mensual -->
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-stone-100 mt-2 font-mono">
            {{ rentabilidad }}%
          </div>
          <!-- Progress bar -->
          <div class="w-full bg-stone-800 h-1.5 rounded-full overflow-hidden mt-3">
            <div class="bg-gradient-to-r from-amber-500 to-emerald-400 h-full rounded-full" :style="{ width: `${rentabilidad}%` }" />
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80 flex items-center justify-between">
          <span>Utilidad neta:</span>
          <strong class="text-emerald-400 font-mono font-bold">{{ formatCOP(totalUtilidad) }}</strong>
        </div>
      </div>

      <!-- 2. Pedidos Activos -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-amber-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Pedidos Activos</span>
            <i class="pi pi-clock text-amber-400" />
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-stone-100 mt-2 font-mono">
            {{ pedidosActivos }}
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80 flex items-center justify-between">
          <span>En confección:</span>
          <span class="text-amber-300 font-semibold">{{ pedidosActivos }} prenda(s) en taller</span>
        </div>
      </div>

      <!-- 3. Ventas Totales -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-amber-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Ventas Totales</span>
            <i class="pi pi-chart-line text-emerald-400" />
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-stone-100 mt-2 font-mono">
            {{ formatCOP(totalVentas) }}
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80 flex items-center justify-between">
          <span>Total órdenes:</span>
          <span class="text-stone-200 font-semibold">{{ pedidos.length }} pedidos registrados</span>
        </div>
      </div>

      <!-- 4. Insumos Críticos -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-red-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Insumos Críticos</span>
            <i class="pi pi-exclamation-circle text-red-400" />
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-red-400 mt-2 font-mono">
            {{ insumosCriticos.length }}
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80">
          <button
            type="button"
            class="text-amber-400 hover:underline font-semibold flex items-center gap-1"
            @click="router.push('/insumos')"
          >
            <span>Ver inventario de insumos</span>
            <i class="pi pi-arrow-right text-[10px]" />
          </button>
        </div>
      </div>
    </div>

    <!-- Flujo de Producción Personalizada (Kanban Summary Bar) -->
    <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2">
          <i class="pi pi-sliders-h" /> Flujo de Producción Personalizada
        </h3>
        <button
          type="button"
          class="text-xs text-amber-400 hover:underline font-semibold flex items-center gap-1"
          @click="router.push('/produccion')"
        >
          <span>Ver Tablero Kanban Completo</span>
          <i class="pi pi-arrow-right text-[10px]" />
        </button>
      </div>

      <div v-if="!pedidos.length" class="text-center py-4 text-xs text-stone-500 bg-stone-900/40 border border-stone-800 rounded-xl">Sin pedidos — creá uno en <code>/produccion</code>.</div>
          <!-- 8-Stage Pipeline Strip -->
          <div v-else class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">1. Cotizado</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ pipelineCounts.COTIZADO }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">2. Reservado</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ pipelineCounts.RESERVADO }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">3. Corte</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ pipelineCounts.CORTE }}</div>
        </div>
        <div class="bg-amber-950/40 border border-amber-500/40 rounded-xl p-2.5 text-center shadow-inner">
          <div class="text-[11px] text-amber-300 font-bold truncate">4. Costura</div>
          <div class="text-base font-bold font-mono text-amber-400 mt-0.5">{{ pipelineCounts.COSTURA }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">5. Acabados</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ pipelineCounts.ACABADOS }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">6. Calidad</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ pipelineCounts.CALIDAD }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">7. Listo</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ pipelineCounts.LISTO }}</div>
        </div>
        <div class="bg-emerald-950/30 border border-emerald-500/30 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-emerald-300 font-bold truncate">8. Entregado</div>
          <div class="text-base font-bold font-mono text-emerald-400 mt-0.5">{{ pipelineCounts.ENTREGADO }}</div>
        </div>
      </div>
    </div>

    <!-- Liquidación & Reparto de Utilidades (REAL: GET /socios + /liquidaciones; oculto si vacío) -->
    <div v-if="tieneRepartoReal" class="bg-gradient-to-br from-stone-900 via-stone-950 to-amber-950/30 border border-amber-500/30 rounded-2xl p-5 shadow-xl space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-stone-800/80 pb-3">
        <div class="flex items-center gap-2 flex-wrap">
          <h3 class="text-sm font-bold uppercase tracking-wider text-amber-300 m-0 flex items-center gap-2">
            <i class="pi pi-wallet" /> Liquidación & Reparto de Utilidades Arpía
          </h3>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Según liquidaciones registradas
          </span>
        </div>
        <div class="text-xs text-stone-300">
          Total Utilidad Taller: <strong class="text-emerald-400 font-mono text-sm">{{ formatCOP(distribucion.total) }}</strong>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Fondo Reinversión Taller (monto real de liquidaciones) -->
        <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-4 space-y-2 hover:border-amber-500/30 transition">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-stone-300">Fondo Reinversión Taller</span>
          </div>
          <div class="text-xl font-bold font-mono text-amber-400">
            {{ formatCOP(distribucion.fondo) }}
          </div>
          <p class="text-[11px] text-stone-400 m-0 leading-tight">
            Acumulado del fondo de taller según liquidaciones registradas.
          </p>
        </div>

        <!-- Socia 1 (real) -->
        <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-4 space-y-2 hover:border-amber-500/30 transition">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-stone-300">{{ distribucion.socia0.nombre }}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-800 text-stone-300">{{ distribucion.socia0.porcentaje }}%</span>
          </div>
          <div class="text-xl font-bold font-mono text-emerald-400">
            {{ formatCOP(distribucion.socia0.monto) }}
          </div>
          <p class="text-[11px] text-stone-400 m-0 leading-tight">
            Liquidado neto acumulado según liquidaciones registradas.
          </p>
        </div>

        <!-- Socia 2 (real) -->
        <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-4 space-y-2 hover:border-amber-500/30 transition">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-stone-300">{{ distribucion.socia1.nombre }}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-800 text-stone-300">{{ distribucion.socia1.porcentaje }}%</span>
          </div>
          <div class="text-xl font-bold font-mono text-emerald-400">
            {{ formatCOP(distribucion.socia1.monto) }}
          </div>
          <p class="text-[11px] text-stone-400 m-0 leading-tight">
            Liquidado neto acumulado según liquidaciones registradas.
          </p>
        </div>
      </div>
    </div>
    <div v-else class="border border-stone-800 rounded-2xl p-6 text-center text-xs text-stone-500 font-mono">
      Sin registro — pendiente: el reparto requiere socias y liquidaciones registradas.
    </div>

    <!-- Bottom Row: Seguimiento de Producción & Rentabilidad Table + Alerts Panel -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left (2 Cols): Orders Table -->
      <div class="lg:col-span-2 bg-stone-900/80 border border-stone-800 rounded-2xl overflow-hidden shadow-lg flex flex-col justify-between">
        <div>
          <div class="p-4 bg-stone-900 border-b border-stone-800 flex items-center justify-between">
            <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2">
              <i class="pi pi-list" /> Seguimiento de Producción & Rentabilidad
            </h3>
            <span class="text-xs text-stone-400">{{ pedidosTabla.length }} órdenes</span>
          </div>

          <div class="hidden overflow-x-auto md:block">
            <table class="w-full min-w-[640px] text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/40">
                  <th class="py-2.5 px-3 sticky left-0 z-10 bg-stone-950/95">Código / Cliente</th>
                  <th class="py-2.5 px-3 min-w-[180px]">Prenda Solicitada</th>
                  <th class="py-2.5 px-3 text-center whitespace-nowrap">Estado</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-stone-800/50 text-stone-200">
                <tr v-for="p in pedidosTabla.slice(0, 6)" :key="p.id" class="hover:bg-stone-800/30">
                  <td class="py-2.5 px-3 sticky left-0 z-10 bg-stone-900/95">
                    <div class="font-mono font-bold text-amber-300">{{ p.codigo }}</div>
                    <div class="text-[11px] text-stone-400 truncate max-w-[130px]">{{ p.cliente_nombre }}</div>
                  </td>
                  <td class="py-2.5 px-3 font-medium text-stone-100 max-w-[180px] truncate min-w-[180px]">
                    {{ p.prenda_nombre }}
                  </td>
                  <td class="py-2.5 px-3 text-center whitespace-nowrap">
                    <span :class="['px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider', getEstadoBadgeClass(p.estado)]">
                      {{ p.estado }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Mobile cards: same pedidosTabla. No horizontal scroll. -->
          <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
            <div v-for="p in pedidosTabla.slice(0, 6)" :key="p.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-1 min-w-0">
              <div class="flex items-start justify-between gap-2 min-w-0">
                <div class="font-mono font-bold text-sm text-amber-300 min-w-0">{{ p.codigo }}</div>
                <span :class="['px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider shrink-0', getEstadoBadgeClass(p.estado)]">{{ p.estado }}</span>
              </div>
              <div class="font-bold text-sm text-stone-100">{{ p.prenda_nombre }}</div>
              <div class="text-sm text-stone-400">{{ p.cliente_nombre }}</div>
            </div>
          </div>
        </div>

        <div class="p-3 bg-stone-950/60 border-t border-stone-800 flex justify-end">
          <button
            type="button"
            class="text-xs text-amber-400 hover:underline font-semibold flex items-center gap-1"
            @click="router.push('/produccion')"
          >
            <span>Ver historial completo de pedidos</span>
            <i class="pi pi-arrow-right text-[10px]" />
          </button>
        </div>
      </div>

      <!-- Right (1 Col): Critical Insumos & Tip Card -->
      <div class="space-y-4">
        <!-- Stock Bajo Crítico -->
        <div class="bg-stone-900/80 border border-red-500/30 rounded-2xl p-4 shadow-lg space-y-3">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-red-400 m-0 flex items-center gap-2">
              <i class="pi pi-exclamation-triangle" /> Stock Bajo Crítico ({{ insumosCriticos.length }} alertas)
            </h4>
          </div>

          <div v-for="it in insumosCriticos" :key="it.id" class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-2">
            <div class="flex justify-between items-start">
              <div>
                <div class="font-bold text-stone-200 text-xs">{{ it.nombre }}</div>
                <div class="text-[11px] text-stone-400">{{ it.proveedor ?? it.nombre_categoria ?? '—' }}</div>
              </div>
              <span class="text-xs font-mono font-bold text-red-400">{{ it.stock_actual }} {{ it.unidad_medida }}</span>
            </div>
            <div class="text-[11px] text-stone-400 flex justify-between">
              <span>Mínimo requerido: {{ it.stock_minimo }} {{ it.unidad_medida }}</span>
              <span class="text-amber-400 font-semibold">Faltante: {{ (it.stock_minimo - it.stock_actual).toFixed(1) }} {{ it.unidad_medida }}</span>
            </div>
            <Button
              label="Generar Orden de Compra"
              icon="pi pi-shopping-cart"
              size="small"
              class="w-full p-button-warning text-xs font-semibold mt-1"
              @click="showSugerirModal = true"
            />
          </div>
        </div>

        <!-- Tip de Rentabilidad Textil (contenido editorial, no dato operativo) -->
        <div class="bg-gradient-to-br from-stone-900 to-amber-950/20 border border-amber-500/30 rounded-2xl p-4 shadow-lg space-y-2.5">
          <div class="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
            <i class="pi pi-lightbulb" /> Tip de Rentabilidad Textil <span class="text-[10px] font-mono font-normal text-stone-400 normal-case">(Consejo editorial)</span>
          </div>
          <p class="text-xs text-stone-300 leading-relaxed m-0">
            "Optimizar el corte de tela en trazos al hilo intercalados ahorra hasta un 8% de merma en rollos de 1.50m."
          </p>
          <div class="flex items-center justify-between pt-1">
            <span class="text-[11px] text-stone-400">Consejo del taller</span>
            <button
              type="button"
              class="text-xs text-amber-400 hover:underline font-bold"
              @click="router.push('/optimizador')"
            >
              Abrir Optimizador →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <NuevoPedidoModal v-model:visible="showNuevoPedidoModal" />
    <SugerirOrdenModal v-model:visible="showSugerirModal" />
  </div>
</template>