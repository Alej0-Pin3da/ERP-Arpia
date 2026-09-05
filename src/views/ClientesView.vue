<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import { useAtelierStore, type ClienteCRM } from '@/stores/atelier'
import NuevoClienteModal from '@/components/atelier/NuevoClienteModal.vue'
import FichaTallasClienteModal from '@/components/atelier/FichaTallasClienteModal.vue'
import { showToast } from '@/utils/toast'
import { useMode } from '@/composables/useMode'
import { useClientes } from '@/composables/useClientes'

const atelier = useAtelierStore()
const { isMock } = useMode()
const clientesApi = useClientes()

const clientesReal = ref<ClienteCRM[]>([])
const cargandoClientes = ref(false)

function normalizeCliente(raw: Record<string, unknown>): ClienteCRM {
  return {
    id: raw.id as number,
    nombre: ((raw.nombre as string) ?? '').trim() || 'Sin nombre',
    tipo: (raw.tipo as string) ?? 'Clienta Habitual',
    telefono: (raw.telefono as string) ?? '',
    email: (raw.email as string) ?? '',
    ciudad: raw.ciudad as string | undefined,
    direccion: raw.direccion as string | undefined,
    pedidos_count: Number(raw.pedidos_count ?? 0),
    total_compras: Number(raw.total_compras ?? 0),
    talla_habitual: (raw.talla_habitual as string) ?? 'M',
    talla_superior: raw.talla_superior as string | undefined,
    talla_inferior: raw.talla_inferior as string | undefined,
    categoria_preferida: (raw.categoria_preferida as string) ?? 'Corsetería & Tops',
    tipo_producto_frecuente: raw.tipo_producto_frecuente as ClienteCRM['tipo_producto_frecuente'],
    notas: raw.notas as string | undefined,
    medidas: raw.medidas as ClienteCRM['medidas'],
  }
}

async function cargarClientesReales() {
  if (isMock.value) return
  cargandoClientes.value = true
  try {
    const res = await clientesApi.list({ limit: 100, offset: 0 })
    clientesReal.value = (res.items as unknown as Record<string, unknown>[]).map(normalizeCliente)
  } catch {
    // keep fallback
  } finally {
    cargandoClientes.value = false
  }
}

onMounted(() => void cargarClientesReales())
watch(isMock, () => void cargarClientesReales())

const clientesList = computed<ClienteCRM[]>(() => (isMock.value ? (atelier.clientes as unknown as ClienteCRM[]) : clientesReal.value))
const search = ref('')
const filtroTalla = ref('TODAS')
const filtroCategoria = ref('TODAS')

const showModal = ref(false)
const showTallasModal = ref(false)
const clienteEditar = ref<ClienteCRM | null>(null)
const clienteSeleccionado = ref<ClienteCRM | null>(null)

watch(showModal, (v) => { if (!v && !isMock.value) void cargarClientesReales() })

async function onFichaGuardada() {
  showTallasModal.value = false
  await cargarClientesReales()
}

const tallasFiltroOptions = [
  { label: 'Todas las Tallas', value: 'TODAS' },
  { label: 'Talla XXS', value: 'XXS' },
  { label: 'Talla XS', value: 'XS' },
  { label: 'Talla S', value: 'S' },
  { label: 'Talla M', value: 'M' },
  { label: 'Talla L', value: 'L' },
  { label: 'Talla XL', value: 'XL' },
  { label: '👜 Sin Talla (Tote Bags)', value: 'SIN_TALLA' },
]

const categoriasFiltroOptions = [
  { label: 'Todas las Categorías', value: 'TODAS' },
  { label: 'Corsetería & Tops', value: 'Corsetería' },
  { label: 'Faldas & Conjuntos', value: 'Faldas' },
  { label: 'Tote Bags de Lona', value: 'Tote Bags' },
  { label: 'Accesorios & Merch', value: 'Accesorios' },
]

const totalClientas = computed(() => clientesList.value.length)

const clientasConTalla = computed(() => {
  return clientesList.value.filter((c) => {
    const t = c.talla_habitual || ''
    return ['XXS', 'XS', 'S', 'M', 'L', 'XL'].some((size) => t.includes(size))
  }).length
})

const clientasSinTalla = computed(() => {
  return clientesList.value.filter((c) => {
    const t = c.talla_habitual || ''
    const cat = c.categoria_preferida || ''
    return t.includes('Sin Talla') || t.includes('Tote') || t.includes('SIN_TALLA') || t.includes('UNICA') || cat.includes('Tote Bags') || cat.includes('Accesorios')
  }).length
})

const totalFacturadoCRM = computed(() => {
  return clientesList.value.reduce((sum, c) => sum + (c.total_compras || 0), 0)
})

const clientesFiltrados = computed(() => {
  return clientesList.value.filter((c) => {
    const q = search.value.trim().toLowerCase()
    const matchesQuery =
      !q ||
      (c.nombre ?? '').toLowerCase().includes(q) ||
      (c.telefono ?? '').toLowerCase().includes(q) ||
      (c.email ?? '').toLowerCase().includes(q) ||
      (c.ciudad ?? '').toLowerCase().includes(q) ||
      (c.talla_habitual ?? '').toLowerCase().includes(q) ||
      (c.notas ?? '').toLowerCase().includes(q)

    const matchesTalla =
      filtroTalla.value === 'TODAS' ||
      (filtroTalla.value === 'SIN_TALLA' && (c.talla_habitual?.includes('Sin Talla') || c.categoria_preferida?.includes('Tote'))) ||
      (c.talla_habitual === filtroTalla.value)

    const matchesCat =
      filtroCategoria.value === 'TODAS' ||
      (c.categoria_preferida && c.categoria_preferida.toLowerCase().includes(filtroCategoria.value.toLowerCase()))

    return matchesQuery && matchesTalla && matchesCat
  })
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function getInitials(nombre: string) {
  const safe = (nombre ?? '').trim()
  if (!safe) return '??'
  const parts = safe.split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return safe.slice(0, 2).toUpperCase()
}

function abrirNuevo() {
  clienteEditar.value = null
  showModal.value = true
}

function editar(c: ClienteCRM) {
  clienteEditar.value = c
  showModal.value = true
}

function abrirFichaTalla(c: ClienteCRM) {
  clienteSeleccionado.value = c
  showTallasModal.value = true
}

function abrirGuiaGeneral() {
  clienteSeleccionado.value = clientesList.value[0] || null
  showTallasModal.value = true
}

async function eliminar(c: ClienteCRM) {
  if (isMock.value) {
    const idx = atelier.clientes.findIndex((x) => x.id === c.id)
    if (idx !== -1) {
      const eliminado = atelier.clientes[idx].nombre
      atelier.clientes.splice(idx, 1)
      showToast('info', 'Clienta eliminada', `${eliminado} ha sido removida del CRM.`)
    }
    return
  }
  try {
    await clientesApi.remove(c.id)
    await cargarClientesReales()
    showToast('info', 'Clienta eliminada', `${c.nombre} eliminada del CRM.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al eliminar clienta'
    showToast('error', 'Error', String(msg))
  }
}

function abrirWhatsApp(c: ClienteCRM) {
  const cleanPhone = (c.telefono || '').replace(/\D/g, '')
  let msgText = ''
  if (c.talla_habitual?.includes('Sin Talla') || c.categoria_preferida?.includes('Tote Bags')) {
    msgText = `¡Hola ${c.nombre}! Te escribimos de Atelier Arpía 👜. Tenemos nuevas Tote Bags ilustradas y accesorios sin talla disponibles. ¿Te gustaría ver el catálogo? ✨`
  } else {
    msgText = `¡Hola ${c.nombre}! Te escribimos de Atelier Arpía. Tenemos novedades en tus prendas favoritas en talla ${c.talla_habitual || 'estándar'}. ¿Deseas coordinar un nuevo pedido? 🪡✨`
  }
  const msg = encodeURIComponent(msgText)
  const url = `https://wa.me/${cleanPhone || '573124567890'}?text=${msg}`
  window.open(url, '_blank')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/95 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div class="space-y-2">
        <div class="flex items-center gap-2.5 flex-wrap">
          <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
            Gestión de Clientas CRM
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider font-mono">
            {{ totalClientas }} Clientas
          </span>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-stone-800 text-stone-300 border border-stone-700 uppercase tracking-wider font-mono">
            Tallas: XXS a XL & Tote Bags
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Control de clientas bajo el modelo de <strong>tallas estándar de marca (XXS, XS, S, M, L, XL)</strong> y productos sin talla como <strong>Tote Bags de lona y accesorios</strong>, con historial comercial y contacto por WhatsApp.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Guía Oficial de Tallas"
          icon="pi pi-book"
          size="small"
          class="p-button-outlined p-button-warning text-xs font-semibold"
          @click="abrirGuiaGeneral"
        />
        <Button
          label="Registrar Clienta"
          icon="pi pi-user-plus"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="abrirNuevo"
        />
      </div>
    </div>

    <!-- Summary Metric Counters -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
      <div class="bg-stone-900/70 border border-stone-800/80 rounded-xl p-3.5 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
          <i class="pi pi-users text-lg" />
        </div>
        <div>
          <span class="block text-[11px] uppercase font-bold text-stone-400">Total Clientas</span>
          <span class="font-mono font-bold text-base text-stone-100">{{ totalClientas }}</span>
        </div>
      </div>

      <div class="bg-stone-900/70 border border-stone-800/80 rounded-xl p-3.5 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
          <i class="pi pi-tag text-lg" />
        </div>
        <div>
          <span class="block text-[11px] uppercase font-bold text-stone-400">Tallas XXS a XL</span>
          <span class="font-mono font-bold text-base text-stone-100">{{ clientasConTalla }}</span>
        </div>
      </div>

      <div class="bg-stone-900/70 border border-stone-800/80 rounded-xl p-3.5 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
          <i class="pi pi-shopping-bag text-lg" />
        </div>
        <div>
          <span class="block text-[11px] uppercase font-bold text-stone-400">Tote Bags & Sin Talla</span>
          <span class="font-mono font-bold text-base text-stone-100">{{ clientasSinTalla }}</span>
        </div>
      </div>

      <div class="bg-stone-900/70 border border-stone-800/80 rounded-xl p-3.5 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
          <i class="pi pi-wallet text-lg" />
        </div>
        <div>
          <span class="block text-[11px] uppercase font-bold text-stone-400">Facturación CRM</span>
          <span class="font-mono font-bold text-base text-emerald-300">{{ formatCOP(totalFacturadoCRM) }}</span>
        </div>
      </div>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-stone-900/60 p-3 rounded-xl border border-stone-800">
      <div class="flex-1 max-w-md">
        <span class="p-input-icon-left w-full">
          <InputText
            v-model="search"
            placeholder="Buscar por nombre, teléfono, ciudad o notas..."
            class="w-full text-xs"
          />
        </span>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Dropdown
          v-model="filtroTalla"
          :options="tallasFiltroOptions"
          option-label="label"
          option-value="value"
          class="text-xs min-w-[160px]"
        />

        <Dropdown
          v-model="filtroCategoria"
          :options="categoriasFiltroOptions"
          option-label="label"
          option-value="value"
          class="text-xs min-w-[170px]"
        />

        <Button
          v-if="search || filtroTalla !== 'TODAS' || filtroCategoria !== 'TODAS'"
          label="Limpiar"
          icon="pi pi-filter-slash"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="search = ''; filtroTalla = 'TODAS'; filtroCategoria = 'TODAS'"
        />
      </div>
    </div>

    <!-- Quick Size Tabs Selector -->
    <div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-mono">
      <span class="text-stone-500 text-[11px] uppercase font-bold mr-1">Filtrar Talla:</span>
      <button
        type="button"
        class="px-2.5 py-1 rounded-lg border transition text-[11px] cursor-pointer"
        :class="filtroTalla === 'TODAS'
          ? 'bg-amber-400 text-stone-950 font-bold border-amber-300 shadow-sm'
          : 'bg-stone-900 text-stone-400 border-stone-800 hover:text-stone-200'"
        @click="filtroTalla = 'TODAS'"
      >
        Todas ({{ clientesList.length }})
      </button>

      <button
        v-for="t in ['XXS', 'XS', 'S', 'M', 'L', 'XL']"
        :key="t"
        type="button"
        class="px-2.5 py-1 rounded-lg border transition text-[11px] font-bold cursor-pointer"
        :class="filtroTalla === t
          ? 'bg-amber-400 text-stone-950 font-black border-amber-300 shadow-sm'
          : 'bg-stone-900 text-stone-300 border-stone-800 hover:border-amber-500/40'"
        @click="filtroTalla = t"
      >
        {{ t }}
      </button>

      <button
        type="button"
        class="px-2.5 py-1 rounded-lg border transition text-[11px] font-bold cursor-pointer"
        :class="filtroTalla === 'SIN_TALLA'
          ? 'bg-amber-400 text-stone-950 font-black border-amber-300 shadow-sm'
          : 'bg-stone-900 text-stone-300 border-stone-800 hover:border-amber-500/40'"
        @click="filtroTalla = 'SIN_TALLA'"
      >
        👜 Sin Talla (Tote Bags)
      </button>
    </div>

    <!-- Grid of Client Cards -->
    <div v-if="clientesFiltrados.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="c in clientesFiltrados"
        :key="c.id"
        class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-amber-500/40 transition group"
      >
        <div class="space-y-4">
          <!-- Top Row: Avatar, Name, Type & Actions -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-full bg-gradient-to-br from-amber-600 to-amber-900 text-amber-200 font-serif font-bold text-sm flex items-center justify-center border border-amber-500/40 shadow-inner">
                {{ getInitials(c.nombre) }}
              </div>
              <div>
                <h3 class="text-sm font-bold text-stone-100 group-hover:text-amber-300 transition m-0">
                  {{ c.nombre }}
                </h3>
                <div class="flex items-center gap-1.5 mt-0.5">
                  <span class="text-[11px] text-stone-400">{{ c.tipo || 'Clienta' }}</span>
                  <span v-if="c.ciudad" class="text-[10px] px-1.5 py-0.2 rounded bg-stone-800 text-stone-300 font-mono">
                    📍 {{ c.ciudad }}
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-1">
              <button
                type="button"
                class="p-1.5 text-stone-400 hover:text-amber-400 rounded transition"
                title="Editar Clienta"
                @click="editar(c)"
              >
                <i class="pi pi-pencil text-xs" />
              </button>
              <button
                type="button"
                class="p-1.5 text-stone-400 hover:text-red-400 rounded transition"
                title="Eliminar Clienta"
                @click="eliminar(c)"
              >
                <i class="pi pi-trash text-xs" />
              </button>
            </div>
          </div>

          <!-- Contact Details & WhatsApp Button -->
          <div class="space-y-2 text-xs">
            <div class="flex items-center justify-between">
              <span class="text-stone-300 font-mono">{{ c.telefono || 'Sin teléfono' }}</span>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-[11px] shadow transition cursor-pointer"
                @click="abrirWhatsApp(c)"
              >
                <i class="pi pi-whatsapp" />
                <span>WhatsApp</span>
              </button>
            </div>
            <div class="text-stone-400 truncate text-[11px]">
              <i class="pi pi-envelope text-[10px] mr-1 text-stone-500" />
              <span>{{ c.email || 'Sin correo registrado' }}</span>
            </div>
          </div>

          <!-- Standard Sizing Profile Showcase (Replaces old bespoke measures) -->
          <div class="bg-stone-950/80 border border-stone-800/80 rounded-xl p-3.5 space-y-2.5">
            <div class="flex items-center justify-between">
              <div class="text-[10px] uppercase font-bold text-amber-400 tracking-wider font-mono flex items-center gap-1.5">
                <i class="pi pi-tag text-[10px]" />
                <span>Talla de Marca & Preferencias</span>
              </div>
              <button
                type="button"
                class="inline-flex items-center gap-1 text-[10px] text-amber-300 hover:text-amber-200 font-mono font-semibold px-2 py-0.5 rounded bg-amber-950/60 border border-amber-500/30 transition cursor-pointer"
                @click="abrirFichaTalla(c)"
              >
                <i class="pi pi-sliders-h text-[10px]" />
                <span>Ficha de Talla</span>
              </button>
            </div>

            <!-- Standard Size Spectrum Bar -->
            <div class="space-y-1">
              <div class="flex items-center justify-between text-[10px] font-mono text-stone-400">
                <span>Talla Asignada:</span>
                <span class="font-bold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  {{ c.talla_habitual || 'S' }}
                </span>
              </div>

              <!-- Interactive / Visual Spectrum -->
              <div class="grid grid-cols-7 gap-1 pt-1">
                <div
                  v-for="t in ['XXS', 'XS', 'S', 'M', 'L', 'XL']"
                  :key="t"
                  class="py-1 text-center font-mono font-bold text-[10px] rounded border"
                  :class="c.talla_habitual === t
                    ? 'bg-amber-400 text-stone-950 border-amber-300 font-black shadow-sm'
                    : 'bg-stone-900 text-stone-500 border-stone-800/80'"
                >
                  {{ t }}
                </div>
                <div
                  class="py-1 text-center font-mono font-bold text-[9px] rounded border truncate"
                  :class="c.talla_habitual?.includes('Sin Talla') || c.categoria_preferida?.includes('Tote')
                    ? 'bg-amber-400 text-stone-950 border-amber-300 font-black shadow-sm'
                    : 'bg-stone-900 text-stone-500 border-stone-800/80'"
                  title="Sin Talla (Tote Bags & Accesorios)"
                >
                  👜
                </div>
              </div>
            </div>

            <!-- Category & Notes -->
            <div class="space-y-1 pt-1 border-t border-stone-800/60 text-[11px]">
              <div class="flex items-center justify-between text-stone-400">
                <span>Interés:</span>
                <span class="font-medium text-stone-200 truncate max-w-[180px]">
                  {{ c.categoria_preferida || 'Corsetería & Tops' }}
                </span>
              </div>

              <div v-if="c.notas" class="text-[10px] text-stone-400 italic bg-stone-900/60 p-1.5 rounded border border-stone-800/40">
                "{{ c.notas }}"
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Stats -->
        <div class="flex items-center justify-between pt-3 border-t border-stone-800/80 mt-4 text-xs">
          <span class="text-stone-400 font-medium">{{ c.pedidos_count }} compras realizadas</span>
          <span class="font-mono font-bold text-amber-300">{{ formatCOP(c.total_compras) }}</span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="text-center py-12 bg-stone-900/40 border border-stone-800 rounded-2xl p-6 space-y-3"
    >
      <div class="w-12 h-12 rounded-full bg-stone-800 flex items-center justify-center mx-auto text-stone-400">
        <i class="pi pi-search text-xl" />
      </div>
      <h3 class="text-sm font-bold text-stone-200">No se encontraron clientas</h3>
      <p class="text-xs text-stone-400 max-w-sm mx-auto">
        Prueba cambiando los filtros de talla (XXS a XL o Sin Talla) o limpiando el texto de búsqueda.
      </p>
      <Button
        label="Limpiar Filtros"
        icon="pi pi-refresh"
        size="small"
        class="p-button-outlined p-button-warning text-xs"
        @click="search = ''; filtroTalla = 'TODAS'; filtroCategoria = 'TODAS'"
      />
    </div>

    <!-- Modals -->
    <NuevoClienteModal v-model:visible="showModal" :cliente-editar="clienteEditar" />
    <FichaTallasClienteModal
      v-model:visible="showTallasModal"
      :cliente="clienteSeleccionado"
      @guardar="onFichaGuardada"
    />
  </div>
</template>
