<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useAtelierStore, type ClienteCRM, type MedidasAnatomicas } from '@/stores/atelier'
import NuevoClienteModal from '@/components/atelier/NuevoClienteModal.vue'
import MedidasAnatomicasModal from '@/components/atelier/MedidasAnatomicasModal.vue'
import { showToast } from '@/utils/toast'

const atelier = useAtelierStore()
const search = ref('')

const showModal = ref(false)
const showMedidasModal = ref(false)
const clienteEditar = ref<ClienteCRM | null>(null)
const clienteMedidas = ref<ClienteCRM | null>(null)

const clientesFiltrados = computed(() => {
  return atelier.clientes.filter((c) => {
    const q = search.value.trim().toLowerCase()
    return (
      !q ||
      c.nombre.toLowerCase().includes(q) ||
      c.telefono.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q)
    )
  })
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function getInitials(nombre: string) {
  const parts = nombre.split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return nombre.slice(0, 2).toUpperCase()
}

function abrirNuevo() {
  clienteEditar.value = null
  showModal.value = true
}

function editar(c: ClienteCRM) {
  clienteEditar.value = c
  showModal.value = true
}

function eliminar(c: ClienteCRM) {
  const idx = atelier.clientes.findIndex((x) => x.id === c.id)
  if (idx !== -1) {
    atelier.clientes.splice(idx, 1)
    showToast('info', 'Clienta eliminada', `${c.nombre} ha sido removida del CRM.`)
  }
}

function abrirWhatsApp(c: ClienteCRM) {
  const cleanPhone = (c.telefono || '').replace(/\D/g, '')
  const msg = encodeURIComponent(`¡Hola ${c.nombre}! Te escribimos de Atelier Arpía para coordinar detalles de tu prenda y medidas. ✨`)
  const url = `https://wa.me/${cleanPhone || '573124567890'}?text=${msg}`
  window.open(url, '_blank')
}

function guardarMedidasCliente(medidas: MedidasAnatomicas) {
  if (clienteMedidas.value) {
    const cl = atelier.clientes.find((c) => c.id === clienteMedidas.value?.id)
    if (cl) {
      cl.medidas = { ...medidas }
    }
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div class="space-y-1.5">
        <div class="flex items-center gap-2.5 flex-wrap">
          <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
            Gestión de Clientes & Ficha de Medidas (CRM)
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
            {{ atelier.clientes.length }} Clientes
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Registro anatómico de medidas, historial de confecciones y comunicación directa por WhatsApp.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Nuevo Cliente"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="abrirNuevo"
        />
      </div>
    </div>

    <!-- Search Input -->
    <div class="w-full md:w-96">
      <span class="p-input-icon-left w-full">
        <InputText
          v-model="search"
          placeholder="Buscar clientes por nombre, teléfono o correo..."
          class="w-full text-xs"
        />
      </span>
    </div>

    <!-- Grid of Client Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="c in clientesFiltrados"
        :key="c.id"
        class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-amber-500/40 transition group"
      >
        <div class="space-y-4">
          <!-- Top Row: Avatar & Actions -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-full bg-gradient-to-br from-amber-600 to-amber-900 text-amber-200 font-serif font-bold text-sm flex items-center justify-center border border-amber-500/40 shadow-inner">
                {{ getInitials(c.nombre) }}
              </div>
              <div>
                <h3 class="text-sm font-bold text-stone-100 group-hover:text-amber-300 transition m-0">
                  {{ c.nombre }}
                </h3>
                <span class="text-xs text-stone-400">{{ c.tipo }}</span>
              </div>
            </div>

            <div class="flex items-center gap-1">
              <button
                type="button"
                class="p-1.5 text-stone-400 hover:text-amber-400 rounded transition"
                title="Editar Ficha"
                @click="editar(c)"
              >
                <i class="pi pi-pencil text-xs" />
              </button>
              <button
                type="button"
                class="p-1.5 text-stone-400 hover:text-red-400 rounded transition"
                title="Eliminar Cliente"
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
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-[11px] shadow transition"
                @click="abrirWhatsApp(c)"
              >
                <i class="pi pi-whatsapp" />
                <span>WhatsApp</span>
              </button>
            </div>
            <div class="text-stone-400 truncate">
              <i class="pi pi-envelope text-[11px] mr-1 text-stone-500" />
              <span>{{ c.email || 'Sin correo registrado' }}</span>
            </div>
          </div>

          <!-- Anatomical Measures Box -->
          <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-2">
            <div class="flex items-center justify-between">
              <div class="text-[10px] uppercase font-bold text-amber-400 tracking-wider">
                Medidas Anatómicas (cm)
              </div>
              <button
                type="button"
                class="inline-flex items-center gap-1 text-[10px] text-amber-300/90 hover:text-amber-200 font-mono font-semibold px-2 py-0.5 rounded bg-amber-950/60 border border-amber-500/30 transition"
                @click="clienteMedidas = c; showMedidasModal = true"
              >
                <i class="pi pi-compass text-[10px]" />
                <span>Silueta & Varillas</span>
              </button>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div class="bg-stone-900/60 p-1.5 rounded border border-stone-800/60">
                <span class="block text-[10px] text-stone-400 font-sans">Busto</span>
                <span class="font-bold text-stone-200">{{ c.medidas?.busto || '-' }}</span>
              </div>
              <div class="bg-stone-900/60 p-1.5 rounded border border-stone-800/60">
                <span class="block text-[10px] text-stone-400 font-sans">Cintura</span>
                <span class="font-bold text-stone-200">{{ c.medidas?.cintura || '-' }}</span>
              </div>
              <div class="bg-stone-900/60 p-1.5 rounded border border-stone-800/60">
                <span class="block text-[10px] text-stone-400 font-sans">Cadera</span>
                <span class="font-bold text-stone-200">{{ c.medidas?.cadera || '-' }}</span>
              </div>
              <div class="bg-stone-900/60 p-1.5 rounded border border-stone-800/60">
                <span class="block text-[10px] text-stone-400 font-sans">Espalda</span>
                <span class="font-bold text-stone-200">{{ c.medidas?.espalda || '-' }}</span>
              </div>
              <div class="bg-stone-900/60 p-1.5 rounded border border-stone-800/60">
                <span class="block text-[10px] text-stone-400 font-sans">Talle</span>
                <span class="font-bold text-stone-200">{{ c.medidas?.talle || '-' }}</span>
              </div>
              <div class="bg-stone-900/60 p-1.5 rounded border border-stone-800/60">
                <span class="block text-[10px] text-stone-400 font-sans">Largo</span>
                <span class="font-bold text-stone-200">{{ c.medidas?.largo || '-' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Stats -->
        <div class="flex items-center justify-between pt-3 border-t border-stone-800/80 mt-4 text-xs">
          <span class="text-stone-400 font-medium">{{ c.pedidos_count }} pedidos realizados</span>
          <span class="font-mono font-bold text-amber-300">{{ formatCOP(c.total_compras) }}</span>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <NuevoClienteModal v-model:visible="showModal" :cliente-editar="clienteEditar" />
    <MedidasAnatomicasModal
      v-model:visible="showMedidasModal"
      :cliente="clienteMedidas"
      @guardar="guardarMedidasCliente"
    />
  </div>
</template>
