<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { subscribeToToasts, type ToastMessage } from '@/utils/toast'

const activeToasts = ref<ToastMessage[]>([])

let unsubscribe: (() => void) | null = null

onMounted(() => {
  unsubscribe = subscribeToToasts((msg) => {
    activeToasts.value.push(msg)
    if (msg.life && msg.life > 0) {
      setTimeout(() => {
        removeToast(msg.id)
      }, msg.life)
    }
  })
})

onUnmounted(() => {
  if (unsubscribe) unsubscribe()
})

function removeToast(id: string) {
  activeToasts.value = activeToasts.value.filter((t) => t.id !== id)
}

function getIcon(sev: string) {
  switch (sev) {
    case 'success':
      return 'pi pi-check-circle'
    case 'warn':
      return 'pi pi-exclamation-triangle'
    case 'error':
      return 'pi pi-times-circle'
    default:
      return 'pi pi-info-circle'
  }
}

function getBorderClass(sev: string) {
  switch (sev) {
    case 'success':
      return 'border-emerald-500/40 bg-emerald-950/90 text-emerald-200'
    case 'warn':
      return 'border-amber-500/40 bg-amber-950/90 text-amber-200'
    case 'error':
      return 'border-red-500/40 bg-red-950/90 text-red-200'
    default:
      return 'border-amber-500/30 bg-stone-900/95 text-stone-200'
  }
}
</script>

<template>
  <div id="arpia-app" class="min-h-screen bg-stone-950 text-stone-100 antialiased selection:bg-amber-500/30 selection:text-amber-200">
    <router-view />

    <!-- Atelier Floating Toasts -->
    <div
      v-if="activeToasts.length"
      class="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full"
    >
      <transition-group
        enter-active-class="transition duration-300 ease-out transform"
        enter-from-class="translate-y-4 opacity-0 scale-95"
        enter-to-class="translate-y-0 opacity-100 scale-100"
        leave-active-class="transition duration-200 ease-in transform"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-for="toast in activeToasts"
          :key="toast.id"
          class="pointer-events-auto rounded-xl border p-3.5 shadow-2xl backdrop-blur-md flex items-start gap-3 text-xs"
          :class="getBorderClass(toast.severity)"
        >
          <i :class="[getIcon(toast.severity), 'text-base shrink-0 mt-0.5']" />
          <div class="flex-1 min-w-0">
            <div class="font-semibold text-stone-100 font-sans tracking-wide">
              {{ toast.summary }}
            </div>
            <div v-if="toast.detail" class="mt-0.5 opacity-90 leading-relaxed font-mono text-[11px]">
              {{ toast.detail }}
            </div>
          </div>
          <button
            type="button"
            class="text-stone-400 hover:text-stone-100 shrink-0 p-1 transition"
            @click="removeToast(toast.id)"
          >
            <i class="pi pi-times text-xs" />
          </button>
        </div>
      </transition-group>
    </div>
  </div>
</template>
