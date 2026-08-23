<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import { useAtelierStore, type VentaAtelier } from '@/stores/atelier'
import NuevaVentaModal from '@/components/atelier/NuevaVentaModal.vue'
import DetalleVentaModal from '@/components/atelier/DetalleVentaModal.vue'
import { showToast } from '@/utils/toast'

const atelier = useAtelierStore()

// Search & Filter state
const search = ref('')
const selectedCanal = ref('TODOS')
const selectedEstado = ref('TODOS')
const selectedSort = ref<'fecha_desc' | 'fecha_asc' | 'total_desc' | 'utilidad_desc'>('fecha_desc')

// Modals state
const showNuevaVentaModal = ref(false)
const showDetalleModal = ref(false)
const showDeleteConfirmModal = ref(false)

const ventaSeleccionadaEditar = ref<VentaAtelier | null>(null)
const ventaSeleccionadaDetalle = ref<VentaAtelier | null>(null)
const ventaAEliminar = ref<VentaAtelier | null>(null)

const canalesFilterOptions = [
  { label: 'Todos los Canales', value: 'TODOS' },
  { label: 'Showroom Pereira', value: 'Showroom Pereira' },
  { label: 'WhatsApp / DM', value: 'WhatsApp / DM' },
  { label: 'Feria / Evento NANA', value: 'Feria / Evento NANA' },
  { label: 'Feria Gótica', value: 'Feria Gótica' },
  { label: 'Feria Showroom', value: 'Feria Showroom' },
  { label: 'Tienda Online / Instagram', value: 'Tienda Online / Instagram' },
  { label: 'Encargo Personalizado', value: 'Encargo Personalizado' },
]

const estadosFilterOptions = [
  { label: 'Todos los Estados', value: 'TODOS' },
  { label: 'Completadas', value: 'COMPLETADA' },
  { label: 'Pendientes', value: 'PENDIENTE' },
  { label: 'Anuladas', value: 'ANULADA' },
]

const sortOptions = [
  { label: '📅 Más recientes primero', value: 'fecha_desc' },
  { label: '📅 Más antiguas primero', value: 'fecha_asc' },
  { label: '💰 Mayor total facturado', value: 'total_desc' },
  { label: '📈 Mayor ganancia neta', value: 'utilidad_desc' },
]

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

const ventasFiltradas = computed(() => {
  let list = [...atelier.ventas]

  // Filter by text search
  if (search.value.trim()) {
    const q = search.value.trim().toLowerCase()
    list = list.filter((v) => {
      const codeMatch = v.codigo.toLowerCase().includes(q)
      const clientMatch = v.cliente_nombre.toLowerCase().includes(q)
      const canalMatch = v.canal.toLowerCase().includes(q)
      const itemsMatch = v.items.some((it) => it.nombre_prenda.toLowerCase().includes(q) || it.color.toLowerCase().includes(q))
      const notesMatch = (v.observaciones || '').toLowerCase().includes(q)
      return codeMatch || clientMatch || canalMatch || itemsMatch || notesMatch
    })
  }

  // Filter by canal
  if (selectedCanal.value !== 'TODOS') {
    list = list.filter((v) => v.canal === selectedCanal.value)
  }

  // Filter by estado
  if (selectedEstado.value !== 'TODOS') {
    list = list.filter((v) => v.estado === selectedEstado.value)
  }

  // Sort
  list.sort((a, b) => {
    if (selectedSort.value === 'fecha_desc') return b.fecha.localeCompare(a.fecha) || b.id - a.id
    if (selectedSort.value === 'fecha_asc') return a.fecha.localeCompare(b.fecha) || a.id - b.id
    if (selectedSort.value === 'total_desc') return b.total_venta - a.total_venta
    if (selectedSort.value === 'utilidad_desc') return b.ganancia_neta - a.ganancia_neta
    return 0
  })

  return list
})

// Metrics for current filtered set
const metricasFiltradas = computed(() => {
  const completadas = ventasFiltradas.value.filter((v) => v.estado === 'COMPLETADA')
  const totalFacturado = completadas.reduce((acc, v) => acc + v.total_venta, 0)
  const totalCosto = completadas.reduce((acc, v) => acc + v.costo_total, 0)
  const totalGanancia = completadas.reduce((acc, v) => acc + v.ganancia_neta, 0)
  const totalPrendas = completadas.reduce((acc, v) => acc + v.items.reduce((s, it) => s + it.cantidad, 0), 0)
  const margen = totalFacturado > 0 ? ((totalGanancia / totalFacturado) * 100).toFixed(1) : '0'

  return {
    totalFacturado,
    totalCosto,
    totalGanancia,
    totalPrendas,
    margen,
    reinversion40: Math.round(totalGanancia * 0.4),
    margara30: Math.round(totalGanancia * 0.3),
    valqui30: Math.round(totalGanancia * 0.3),
  }
})

// Handlers
function abrirNuevaVenta() {
  ventaSeleccionadaEditar.value = null
  showNuevaVentaModal.value = true
}

function abrirEditarVenta(v: VentaAtelier) {
  ventaSeleccionadaEditar.value = v
  showNuevaVentaModal.value = true
}

function abrirDetalle(v: VentaAtelier) {
  ventaSeleccionadaDetalle.value = v
  showDetalleModal.value = true
}

function abrirEditarDesdeDetalle(v: VentaAtelier) {
  showDetalleModal.value = false
  abrirEditarVenta(v)
}

function solicitarEliminarVenta(v: VentaAtelier) {
  ventaAEliminar.value = v
  showDeleteConfirmModal.value = true
}

function confirmarEliminar() {
  if (ventaAEliminar.value) {
    const cod = ventaAEliminar.value.codigo
    const ok = atelier.eliminarVenta(ventaAEliminar.value.id)
    if (ok) {
      showToast('info', 'Venta Eliminada', `La venta ${cod} ha sido removida del registro.`)
    }
  }
  showDeleteConfirmModal.value = false
  ventaAEliminar.value = null
}

function exportarCSV() {
  const headers = [
    'Codigo',
    'Fecha',
    'Cliente',
    'Canal',
    'MetodoPago',
    'Estado',
    'Prendas',
    'Subtotal',
    'Descuento_Pct',
    'Descuento_Valor',
    'Total_Facturado',
    'Costo_Produccion',
    'Ganancia_Neta',
    'Margen_Pct',
    'Reinversion_40',
    'Margara_30',
    'Valqui_30',
    'Observaciones',
  ]

  const rows = atelier.ventas.map((v) => [
    `"${v.codigo}"`,
    `"${v.fecha}"`,
    `"${v.cliente_nombre}"`,
    `"${v.canal}"`,
    `"${v.metodo_pago}"`,
    `"${v.estado}"`,
    `"${v.items.map((i) => `${i.cantidad}x ${i.nombre_prenda} (${i.talla})`).join(' + ')}"`,
    v.subtotal,
    v.descuento_porcentaje,
    v.descuento_valor,
    v.total_venta,
    v.costo_total,
    v.ganancia_neta,
    v.margen_pct,
    v.reinversion_40,
    v.margarita_30,
    v.valqui_30,
    `"${(v.observaciones || '').replace(/"/g, '""')}"`,
  ])

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n')
  const encodedUri = encodeURI(csvContent)
  const link = document.createElement('a')
  link.setAttribute('href', encodedUri)
  link.setAttribute('download', `ARPIA_VENTAS_HISTORICO_${new Date().toISOString().split('T')[0]}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  showToast('success', 'Archivo CSV Descargado', 'Histórico de ventas exportado exitosamente.')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div class="space-y-1.5">
        <div class="flex items-center gap-2.5 flex-wrap">
          <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0 flex items-center gap-2">
            <span>Registro de Ventas Realizadas</span>
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider font-mono">
            {{ atelier.ventas.length }} Ventas Totales
          </span>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 font-mono">
            {{ formatCOP(atelier.totalVentasRealizadas) }}
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Historial financiero de ventas, facturación en showroom/ferias, recibos de autor y liquidación de socias (40/30/30).
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <Button
          label="Exportar CSV"
          icon="pi pi-download"
          size="small"
          class="p-button-outlined p-button-secondary text-xs font-semibold"
          @click="exportarCSV"
        />
        <Button
          label="Registrar Nueva Venta"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold shadow-lg shadow-amber-950/40"
          @click="abrirNuevaVenta"
        />
      </div>
    </div>

    <!-- 5 KPI Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
      <!-- Total Facturado -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md flex flex-col justify-between">
        <div class="text-[11px] text-stone-400 font-bold uppercase tracking-wider font-mono">Total Facturado</div>
        <div class="text-2xl font-extrabold text-amber-300 mt-2 font-mono">
          {{ formatCOP(metricasFiltradas.totalFacturado) }}
        </div>
        <div class="text-[11px] text-stone-500 mt-1 font-mono">
          {{ metricasFiltradas.totalPrendas }} prendas vendidas
        </div>
      </div>

      <!-- Ganancia Neta -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md flex flex-col justify-between">
        <div class="text-[11px] text-stone-400 font-bold uppercase tracking-wider font-mono">Ganancia Neta</div>
        <div class="text-2xl font-extrabold text-emerald-400 mt-2 font-mono">
          {{ formatCOP(metricasFiltradas.totalGanancia) }}
        </div>
        <div class="text-[11px] text-stone-500 mt-1 font-mono">
          Costo: {{ formatCOP(metricasFiltradas.totalCosto) }}
        </div>
      </div>

      <!-- Margen Promedio -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md flex flex-col justify-between">
        <div class="text-[11px] text-stone-400 font-bold uppercase tracking-wider font-mono">Margen Utilidad</div>
        <div class="text-2xl font-extrabold text-stone-100 mt-2 font-mono">
          {{ metricasFiltradas.margen }}%
        </div>
        <div class="text-[11px] text-emerald-400 mt-1 font-mono">
          Rentabilidad de marca
        </div>
      </div>

      <!-- Fondo Reinversión 40% -->
      <div class="bg-gradient-to-br from-stone-900/90 to-amber-950/40 border border-amber-500/30 rounded-2xl p-4 shadow-md flex flex-col justify-between">
        <div class="text-[11px] text-amber-300 font-bold uppercase tracking-wider font-mono">🏛️ Fondo Taller 40%</div>
        <div class="text-xl font-extrabold text-amber-400 mt-2 font-mono">
          {{ formatCOP(metricasFiltradas.reinversion40) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1 font-mono">
          Reinversión en telas & insumos
        </div>
      </div>

      <!-- Socias 30% / 30% -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md flex flex-col justify-between">
        <div class="text-[11px] text-stone-400 font-bold uppercase tracking-wider font-mono">🪡 Margara & Valqui (30/30)</div>
        <div class="text-lg font-extrabold text-stone-200 mt-2 font-mono">
          {{ formatCOP(metricasFiltradas.margara30) }} <span class="text-xs text-stone-500 font-normal">c/u</span>
        </div>
        <div class="text-[11px] text-stone-500 mt-1 font-mono">
          Total socias: {{ formatCOP(metricasFiltradas.margara30 + metricasFiltradas.valqui30) }}
        </div>
      </div>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="bg-stone-900/60 p-4 rounded-2xl border border-stone-800 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 text-xs">
      <!-- Search -->
      <div class="w-full md:w-80">
        <span class="p-input-icon-left w-full">
          <InputText
            v-model="search"
            placeholder="Buscar por código, prenda, cliente o canal..."
            class="w-full text-xs"
          />
        </span>
      </div>

      <!-- Filter dropdowns -->
      <div class="flex flex-wrap items-center gap-2">
        <Dropdown
          v-model="selectedCanal"
          :options="canalesFilterOptions"
          option-label="label"
          option-value="value"
          class="text-xs w-44"
        />

        <Dropdown
          v-model="selectedEstado"
          :options="estadosFilterOptions"
          option-label="label"
          option-value="value"
          class="text-xs w-36"
        />

        <Dropdown
          v-model="selectedSort"
          :options="sortOptions"
          option-label="label"
          option-value="value"
          class="text-xs w-52"
        />

        <Button
          v-if="search || selectedCanal !== 'TODOS' || selectedEstado !== 'TODOS'"
          label="Limpiar"
          icon="pi pi-filter-slash"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="search = ''; selectedCanal = 'TODOS'; selectedEstado = 'TODOS'"
        />
      </div>
    </div>

    <!-- Sales Table / List Card -->
    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-4 sm:p-5 shadow-xl space-y-4">
      <div v-if="ventasFiltradas.length === 0" class="text-center py-16 text-stone-500 font-mono text-xs space-y-3">
        <div class="text-3xl">🛍️</div>
        <div class="text-stone-300 font-serif font-bold text-sm">No se encontraron ventas</div>
        <p class="text-stone-500 max-w-sm mx-auto">
          No hay registros de ventas que coincidan con los filtros seleccionados o no se han ingresado aún.
        </p>
        <Button
          label="Registrar Primera Venta"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="abrirNuevaVenta"
        />
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-xs text-left border-collapse font-mono">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 text-[11px] uppercase tracking-wider">
              <th class="py-3 px-3">Venta / Fecha</th>
              <th class="py-3 px-3">Cliente & Canal</th>
              <th class="py-3 px-3">Prendas / Artículos</th>
              <th class="py-3 px-3 text-right">Descuento</th>
              <th class="py-3 px-3 text-right">Total Venta</th>
              <th class="py-3 px-3 text-right">Utilidad Neta</th>
              <th class="py-3 px-3 text-center">Estado</th>
              <th class="py-3 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60">
            <tr
              v-for="v in ventasFiltradas"
              :key="v.id"
              class="hover:bg-stone-800/40 transition group"
            >
              <!-- Code & Date -->
              <td class="py-3.5 px-3">
                <div class="flex items-center gap-2">
                  <span class="font-bold text-amber-400 tracking-wide text-xs">
                    {{ v.codigo }}
                  </span>
                </div>
                <div class="text-[11px] text-stone-500 mt-0.5">
                  {{ v.fecha }}
                </div>
              </td>

              <!-- Client & Channel -->
              <td class="py-3.5 px-3">
                <div class="font-serif font-bold text-stone-100 text-sm">
                  {{ v.cliente_nombre }}
                </div>
                <div class="flex items-center gap-1.5 mt-1">
                  <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-stone-800 text-amber-300/90 border border-stone-700">
                    {{ v.canal }}
                  </span>
                  <span class="text-[10px] text-stone-500">
                    · {{ v.metodo_pago }}
                  </span>
                </div>
              </td>

              <!-- Garments & Items -->
              <td class="py-3.5 px-3 max-w-xs">
                <div class="space-y-1">
                  <div
                    v-for="it in v.items"
                    :key="it.id"
                    class="text-xs text-stone-200 font-serif"
                  >
                    <span class="font-bold font-mono text-amber-400 mr-1">{{ it.cantidad }}x</span>
                    <span>{{ it.nombre_prenda }}</span>
                    <span class="ml-1 text-[10px] font-mono text-stone-400 bg-stone-950 px-1.5 py-0.5 rounded border border-stone-800">
                      {{ it.talla }}
                    </span>
                  </div>
                </div>
                <div v-if="v.observaciones" class="text-[10px] text-stone-500 italic mt-1 truncate max-w-[220px]">
                  💬 {{ v.observaciones }}
                </div>
              </td>

              <!-- Discount -->
              <td class="py-3.5 px-3 text-right">
                <div v-if="v.descuento_valor > 0" class="text-rose-400 font-bold">
                  -{{ formatCOP(v.descuento_valor) }}
                  <div class="text-[10px] text-rose-500">({{ v.descuento_porcentaje }}%)</div>
                </div>
                <div v-else class="text-stone-600">—</div>
              </td>

              <!-- Total Venta -->
              <td class="py-3.5 px-3 text-right">
                <div class="text-base font-bold text-amber-300">
                  {{ formatCOP(v.total_venta) }}
                </div>
                <div class="text-[10px] text-stone-500">
                  Costo: {{ formatCOP(v.costo_total) }}
                </div>
              </td>

              <!-- Net Utility & Margin -->
              <td class="py-3.5 px-3 text-right">
                <div class="text-sm font-bold text-emerald-400">
                  {{ formatCOP(v.ganancia_neta) }}
                </div>
                <div class="inline-block mt-0.5 px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-600/30">
                  {{ v.margen_pct }}%
                </div>
              </td>

              <!-- State Tag & Quick Change -->
              <td class="py-3.5 px-3 text-center">
                <span
                  class="px-2.5 py-1 rounded-full text-[10px] font-bold border inline-block"
                  :class="v.estado === 'COMPLETADA' ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/30' : v.estado === 'PENDIENTE' ? 'bg-amber-950/80 text-amber-300 border-amber-500/30' : 'bg-rose-950/80 text-rose-300 border-rose-500/30'"
                >
                  {{ v.estado }}
                </span>
              </td>

              <!-- Action Buttons (View Receipt, Edit, Delete) -->
              <td class="py-3.5 px-3 text-right">
                <div class="flex items-center justify-end gap-1">
                  <!-- View Receipt -->
                  <Button
                    icon="pi pi-receipt"
                    size="small"
                    class="p-button-text p-button-warning text-xs p-1"
                    title="Ver Comprobante / Recibo"
                    @click="abrirDetalle(v)"
                  />

                  <!-- Edit -->
                  <Button
                    icon="pi pi-pencil"
                    size="small"
                    class="p-button-text p-button-info text-xs p-1"
                    title="Editar Venta"
                    @click="abrirEditarVenta(v)"
                  />

                  <!-- Delete -->
                  <Button
                    icon="pi pi-trash"
                    size="small"
                    class="p-button-text p-button-danger text-xs p-1"
                    title="Eliminar Venta"
                    @click="solicitarEliminarVenta(v)"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modals -->
    <NuevaVentaModal
      :visible="showNuevaVentaModal"
      :venta-editar="ventaSeleccionadaEditar"
      @update:visible="(val) => showNuevaVentaModal = val"
    />

    <DetalleVentaModal
      :visible="showDetalleModal"
      :venta="ventaSeleccionadaDetalle"
      @update:visible="(val) => showDetalleModal = val"
      @editar="abrirEditarDesdeDetalle"
    />

    <!-- Delete Confirmation Modal -->
    <Dialog
      v-model:visible="showDeleteConfirmModal"
      modal
      header="⚠️ Confirmar Eliminación de Venta"
      :style="{ width: '90vw', maxWidth: '440px' }"
    >
      <div class="space-y-3 pt-2 text-xs text-stone-300">
        <p>
          ¿Estás seguro de que deseas eliminar la venta <strong class="text-amber-400 font-mono">{{ ventaAEliminar?.codigo }}</strong>?
        </p>
        <p class="text-[11px] text-stone-500 font-mono">
          Cliente: {{ ventaAEliminar?.cliente_nombre }} · Total: {{ formatCOP(ventaAEliminar?.total_venta || 0) }}
        </p>
        <p class="text-[11px] text-rose-400 font-semibold">
          Esta acción removerá el registro financiero del historial de ventas.
        </p>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
          <Button
            label="Cancelar"
            icon="pi pi-times"
            size="small"
            class="p-button-text p-button-secondary text-xs"
            @click="showDeleteConfirmModal = false"
          />
          <Button
            label="Sí, Eliminar Venta"
            icon="pi pi-trash"
            size="small"
            class="p-button-danger text-xs font-semibold"
            @click="confirmarEliminar"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>
