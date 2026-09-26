<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-empty */
import { computed, ref, onMounted } from 'vue'
import { useInsumos } from '@/composables/useInsumos'
import { useProduccion } from '@/composables/useProduccion'
import { useProductos } from '@/composables/useProductos'
import { useAnaliticos } from '@/composables/useAnaliticos'

const insumosApi = useInsumos()
const produccionApi = useProduccion()
const productosApi = useProductos()
const analiticosApi = useAnaliticos()
const insumos = ref<any[]>([])
const pedidos = ref<any[]>([])
const resumen = ref<any | null>(null)
const ventasMensuales = ref<any[]>([])
const topProductos = ref<any[]>([])
const topInsumos = ref<any[]>([])
const finanzasMensuales = ref<any[]>([])
const margenReal = ref<any[]>([])
const insumosCriticos = ref<any[]>([])
async function cargarAnalisis() {
  try {
    const [ir, pr] = await Promise.all([
      insumosApi.list({ limit: 100 }),
      produccionApi.list({ limit: 100 }),
    ])
    insumos.value = (ir as any).items ?? []
    pedidos.value = (pr as any).items ?? []
  } catch {}
  // Agregados reales del backend (ANA-1..6). Cada uno con fallback silencioso:
  // si falla, la sección muestra vacío en vez de romper la vista.
  try { resumen.value = await analiticosApi.getResumen() } catch { resumen.value = null }
  try { ventasMensuales.value = (await analiticosApi.getVentasMensuales() as any) ?? [] } catch { ventasMensuales.value = [] }
  try { topProductos.value = (await analiticosApi.getTopProductos() as any) ?? [] } catch { topProductos.value = [] }
  try { topInsumos.value = (await analiticosApi.getTopInsumos() as any) ?? [] } catch { topInsumos.value = [] }
  try { finanzasMensuales.value = (await analiticosApi.getFinanzasMensuales() as any) ?? [] } catch { finanzasMensuales.value = [] }
  try { margenReal.value = (await analiticosApi.getMargenPorProducto() as any) ?? [] } catch { margenReal.value = [] }
  try { insumosCriticos.value = (await analiticosApi.getInsumosBajoStock() as any) ?? [] } catch { insumosCriticos.value = [] }
}
onMounted(() => { void cargarAnalisis(); void cargarProductosAnalisis() })

const pedidosSrc = computed(() => (pedidos.value as any[]))
const insumosAlertasCount = computed(() => (insumos.value as any[]).filter((i: any) => Number(i.stock_actual ?? i.stock ?? 0) <= Number(i.stock_minimo ?? 0)).length)
const productosAnalisis = ref<any[]>([])
async function cargarProductosAnalisis() {
  try {
    const r = await productosApi.list({ limit: 100 })
    productosAnalisis.value = (r.items as any) ?? []
  } catch { productosAnalisis.value = [] }
}
// append to existing cargarAnalisis
// Numeric de Postgres serializa como string: normalizar a number para que
// formatCOP y el margen no reciban strings ni nulls.
const recetasDisplay = computed(() => productosAnalisis.value.map((p: any) => ({
  id: p.id,
  nombre: p.nombre,
  costo_estimado_materiales: Number(p.costo_insumos ?? 0),
  tiempo_estimado_confeccion_horas: p.tiempo_confeccion_min ? Math.round(Number(p.tiempo_confeccion_min) / 60 * 10) / 10 : 1,
  precio_venta_sugerido: Number(p.precio_venta_sugerido ?? 0),
})))

// Nombre de producto para los agregados que solo traen IDs (top/margen real).
const nombreProducto = (id: number): string =>
  String(productosAnalisis.value.find((p: any) => Number(p.id) === Number(id))?.nombre ?? `Producto #${id}`)
const topProductosDisplay = computed(() => (topProductos.value as any[]).slice(0, 5).map((t: any) => ({
  producto_id: t.producto_id,
  nombre: nombreProducto(t.producto_id),
  unidades: Number(t.unidades ?? 0),
  ingresos: Number(t.ingresos ?? 0),
})))
const topInsumosDisplay = computed(() => (topInsumos.value as any[]).slice(0, 5).map((t: any) => ({
  nombre: String(t.nombre ?? `Insumo #${t.insumo_id}`),
  unidad: String(t.unidad_medida ?? ''),
  cantidad: Number(t.cantidad ?? 0),
})))
const ventasMensualesDisplay = computed(() => (ventasMensuales.value as any[]).slice(-6).map((v: any) => ({
  mes: String(v.mes ?? '').slice(0, 7),
  total: Number(v.total ?? 0),
  cantidad: Number(v.cantidad ?? 0),
})))
const finanzasMensualesDisplay = computed(() => (finanzasMensuales.value as any[]).slice(-6).map((f: any) => ({
  mes: String(f.mes ?? '').slice(0, 7),
  ingresos: Number(f.ingresos ?? 0),
  gastos: Number(f.gastos ?? 0),
})))
const margenRealDisplay = computed(() => (margenReal.value as any[]).slice(0, 5).map((m: any) => ({
  nombre: nombreProducto(m.producto_id),
  margen_total: Number(m.margen_total ?? 0),
  margen_promedio: Number(m.margen_promedio ?? 0),
})))

const normEstado = (e: unknown) => String(e ?? '').toLowerCase()
// El backend manda el enum de estado (completado/en_produccion...):
// se normaliza para que los contadores no queden en 0.
const esCompletado = (e: unknown) => ['entregado', 'completado', 'listo'].includes(normEstado(e))
const esEnProceso = (e: unknown) =>
  ['pendiente', 'en_produccion', 'corte', 'costura', 'confeccion', 'prueba', 'acabados', 'calidad'].includes(normEstado(e))

const metricas = computed(() => {
  const pedidosCompletados = pedidosSrc.value.filter((p: any) => esCompletado(p.estado)).length
  const pedidosEnProceso = pedidosSrc.value.filter((p: any) => esEnProceso(p.estado)).length
  const stockPrendas = productosAnalisis.value.reduce((acc: number, p: any) => acc + (Number(p.stock_actual ?? 0) || 0), 0)
  const insumosAlertas = insumosAlertasCount.value

  return {
    pedidosCompletados,
    pedidosEnProceso,
    stockPrendas,
    insumosAlertas,
  }
})

function formatCOP(v: number): string {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Análisis de Rendimiento de Arpía
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Métricas de productividad de costura, rotación de insumos y márgenes por tipo de prenda.
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Prendas en Confección Activa</div>
        <div class="text-2xl font-serif font-bold text-amber-400 mt-1">{{ metricas.pedidosEnProceso }}</div>
      </div>
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Pedidos Entregados</div>
        <div class="text-2xl font-serif font-bold text-emerald-400 mt-1">{{ metricas.pedidosCompletados }}</div>
      </div>
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Unidades en Stock (lote)</div>
        <div class="text-2xl font-serif font-bold text-stone-200 mt-1">{{ metricas.stockPrendas }}</div>
      </div>
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Insumos con Stock Crítico</div>
        <div class="text-2xl font-serif font-bold text-red-400 mt-1">{{ metricas.insumosAlertas }}</div>
      </div>
    </div>

    <!-- Resumen real del período (backend ANA resumen) -->
    <div v-if="resumen" class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
      <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2">
        <i class="pi pi-wallet text-emerald-400" />
        Resumen del Período (ventas reales, sin anuladas ni regalos)
      </h2>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
        <div><div class="text-[11px] uppercase font-bold text-stone-400">Ventas</div><div class="font-mono font-bold text-stone-100">{{ formatCOP(Number(resumen.ventas_total ?? 0)) }}</div></div>
        <div><div class="text-[11px] uppercase font-bold text-stone-400">Cant. ventas</div><div class="font-mono font-bold text-stone-100">{{ resumen.cantidad_ventas ?? 0 }}</div></div>
        <div><div class="text-[11px] uppercase font-bold text-stone-400">Ticket prom.</div><div class="font-mono font-bold text-stone-100">{{ formatCOP(Number(resumen.ticket_promedio ?? 0)) }}</div></div>
        <div><div class="text-[11px] uppercase font-bold text-stone-400">Margen total</div><div class="font-mono font-bold text-emerald-400">{{ formatCOP(Number(resumen.margen_total ?? 0)) }}</div></div>
        <div><div class="text-[11px] uppercase font-bold text-stone-400">Gastos</div><div class="font-mono font-bold text-red-300">{{ formatCOP(Number(resumen.gastos_total ?? 0)) }}</div></div>
        <div><div class="text-[11px] uppercase font-bold text-stone-400">Resultado neto</div><div class="font-mono font-bold text-amber-300">{{ formatCOP(Number(resumen.resultado_neto ?? 0)) }}</div></div>
      </div>
    </div>

    <!-- Ventas + finanzas mensuales -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-3">
        <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2">
          <i class="pi pi-chart-bar text-amber-400" />
          Ventas por Mes
        </h2>
        <div v-if="!ventasMensualesDisplay.length" class="text-xs text-stone-500">Sin ventas registradas.</div>
        <div v-for="v in ventasMensualesDisplay" :key="v.mes" class="flex items-center justify-between text-xs font-mono">
          <span class="text-stone-400">{{ v.mes }}</span>
          <span class="text-stone-200">{{ formatCOP(v.total) }} · {{ v.cantidad }} ventas</span>
        </div>
      </div>
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-3">
        <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2">
          <i class="pi pi-chart-line text-emerald-400" />
          Ingresos vs Gastos por Mes
        </h2>
        <div v-if="!finanzasMensualesDisplay.length" class="text-xs text-stone-500">Sin movimientos registrados.</div>
        <div v-for="f in finanzasMensualesDisplay" :key="f.mes" class="flex items-center justify-between text-xs font-mono">
          <span class="text-stone-400">{{ f.mes }}</span>
          <span><span class="text-emerald-300">{{ formatCOP(f.ingresos) }}</span><span class="text-stone-500"> vs </span><span class="text-red-300">{{ formatCOP(f.gastos) }}</span></span>
        </div>
      </div>
    </div>

    <!-- Tops reales -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-3">
        <h2 class="text-sm font-serif font-semibold text-stone-100">Top Productos (unidades)</h2>
        <div v-if="!topProductosDisplay.length" class="text-xs text-stone-500">Sin ventas por producto.</div>
        <div v-for="t in topProductosDisplay" :key="t.producto_id" class="flex items-center justify-between text-xs">
          <span class="text-stone-200 truncate">{{ t.nombre }}</span>
          <span class="font-mono text-stone-400">{{ t.unidades }} u · {{ formatCOP(t.ingresos) }}</span>
        </div>
      </div>
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-3">
        <h2 class="text-sm font-serif font-semibold text-stone-100">Top Insumos (compras)</h2>
        <div v-if="!topInsumosDisplay.length" class="text-xs text-stone-500">Sin compras registradas.</div>
        <div v-for="(t, i) in topInsumosDisplay" :key="i" class="flex items-center justify-between text-xs">
          <span class="text-stone-200 truncate">{{ t.nombre }}</span>
          <span class="font-mono text-stone-400">{{ t.cantidad }} {{ t.unidad }}</span>
        </div>
      </div>
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-3">
        <h2 class="text-sm font-serif font-semibold text-stone-100">Margen Real por Producto</h2>
        <div v-if="!margenRealDisplay.length" class="text-xs text-stone-500">Sin margen snapshot todavía.</div>
        <div v-for="(m, i) in margenRealDisplay" :key="i" class="flex items-center justify-between text-xs">
          <span class="text-stone-200 truncate">{{ m.nombre }}</span>
          <span class="font-mono text-emerald-300">{{ formatCOP(m.margen_total) }}</span>
        </div>
        <div v-if="insumosCriticos.length" class="pt-2 border-t border-stone-800">
          <div class="text-[11px] uppercase font-bold text-red-300 mb-1">Detalle stock crítico ({{ insumosCriticos.length }})</div>
          <div v-for="(c, i) in (insumosCriticos as any[]).slice(0, 5)" :key="i" class="flex items-center justify-between text-xs font-mono">
            <span class="text-stone-300 truncate">{{ (c as any).nombre }}</span>
            <span class="text-red-300">{{ Number((c as any).stock_actual ?? 0) }} / mín {{ Number((c as any).stock_minimo ?? 0) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Product Margins Analysis -->
    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
      <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2">
        <i class="pi pi-chart-line text-amber-400" />
        Rentabilidad por Ficha Técnica / Receta BOM
      </h2>

      <div class="hidden overflow-x-auto md:block">
        <table class="w-full min-w-[640px] text-xs text-left border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 font-mono">
              <th class="py-2.5 px-3 sticky left-0 z-10 bg-stone-950/95 min-w-[180px]">Prenda / Receta</th>
              <th class="py-2.5 px-3 text-right whitespace-nowrap">Costo Insumos</th>
              <th class="py-2.5 px-3 whitespace-nowrap">Horas Confección</th>
              <th class="py-2.5 px-3 text-right whitespace-nowrap">Precio Sugerido</th>
              <th class="py-2.5 px-3 text-right whitespace-nowrap">Margen Bruto</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60 font-mono">
                <tr v-if="!recetasDisplay.length">
                  <td colspan="5" class="py-8 text-center text-stone-500">Sin recetas para analizar.</td>
                </tr>
            <tr v-for="r in recetasDisplay" :key="r.id" class="hover:bg-stone-900/50">
              <td class="py-3 px-3 font-serif text-sm font-semibold text-stone-200 sticky left-0 z-10 bg-stone-900/95 min-w-[180px]">{{ r.nombre }}</td>
              <td class="py-3 px-3 text-stone-300 text-right whitespace-nowrap">{{ formatCOP(Number(r.costo_estimado_materiales ?? 0)) }}</td>
              <td class="py-3 px-3 text-stone-400 whitespace-nowrap">{{ r.tiempo_estimado_confeccion_horas }}h</td>
              <td class="py-3 px-3 text-amber-300 font-bold text-right whitespace-nowrap">{{ formatCOP(Number(r.precio_venta_sugerido ?? 0)) }}</td>
              <td class="py-3 px-3 text-emerald-400 font-bold text-right whitespace-nowrap">
                {{ formatCOP(Number(r.precio_venta_sugerido ?? 0) - Number(r.costo_estimado_materiales ?? 0)) }}
                <span class="text-[10px] opacity-75">
                  ({{ Number(r.precio_venta_sugerido ?? 0) > 0 ? Math.round(((Number(r.precio_venta_sugerido ?? 0) - Number(r.costo_estimado_materiales ?? 0)) / Number(r.precio_venta_sugerido ?? 0)) * 100) : 0 }}%)
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Mobile cards: same recetasDisplay. No horizontal scroll. -->
      <div class="space-y-3 md:hidden max-w-full min-w-0">
        <div v-if="!recetasDisplay.length" class="text-center py-8 text-sm text-stone-500">Sin recetas para analizar.</div>
        <div v-for="r in recetasDisplay" :key="r.id" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
          <div class="font-bold text-sm text-stone-100">{{ r.nombre }}</div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Costo insumos</span>
            <span class="font-mono text-stone-300">{{ formatCOP(Number(r.costo_estimado_materiales ?? 0)) }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Confección</span>
            <span class="text-stone-300">{{ r.tiempo_estimado_confeccion_horas }}h</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Precio sugerido</span>
            <span class="font-mono font-bold text-amber-300">{{ formatCOP(Number(r.precio_venta_sugerido ?? 0)) }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Margen bruto</span>
            <span class="font-mono font-bold text-emerald-400">{{ formatCOP(Number(r.precio_venta_sugerido ?? 0) - Number(r.costo_estimado_materiales ?? 0)) }} ({{ Number(r.precio_venta_sugerido ?? 0) > 0 ? Math.round(((Number(r.precio_venta_sugerido ?? 0) - Number(r.costo_estimado_materiales ?? 0)) / Number(r.precio_venta_sugerido ?? 0)) * 100) : 0 }}%)</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
