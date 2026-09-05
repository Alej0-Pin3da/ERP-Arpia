/**
 * mockGuard — fail-loud in REAL mode.
 *
 * When isMock === false (VITE_USE_MOCK=false + /api/__mode === real),
 * any read/write of critical atelier.* props logs a console.error + toast
 * and a stack trace. This makes mock leaks visible instead of silently
 * rendering ghost data in REAL.
 *
 * Call installMockGuard() once after Pinia is installed (AppLayout onMounted).
 */
import { watch } from 'vue'
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'

const CRITICAL_PROPS = [
  'recetas',
  'clientes',
  'ventas',
  'insumos',
  'prendasListas',
  'pedidos',
  'socias',
  'liquidaciones',
  'anticipos',
  'proveedoresMaestros',
  'canalesVentaMaestros',
  'metodosPagoMaestros',
  // Ojo: el store expone estos con sufijo Maestros (sin él, el guard los saltea en silencio).
  'categoriasColeccionMaestros',
  'ubicacionesTallerMaestros',
  'tallasEstandarMaestros',
  'productosSinTallaMaestros',
  'parametrosCosteo',
  // computed helpers
  'insumosCriticos',
  'totalVentasRealizadas',
  'totalVentas',
  'totalUtilidad',
  'rentabilidadPromedio',
  'valorTotalInventario',
  'distribucionSocias',
  'pipelineCounts',
] as const

let installed = false

export function installMockGuard(): void {
  if (installed) return
  installed = true

  const atelier = useAtelierStore() as unknown as Record<string, unknown>
  const { isMock } = useMode()
  const warned = new Set<string>()

  CRITICAL_PROPS.forEach((prop) => {
    if (!(prop in atelier)) return
    let backing = atelier[prop]
    // Preserve original descriptor if it was a computed/ref
    Object.defineProperty(atelier, prop, {
      get() {
        if (!isMock.value) {
          if (!warned.has(prop)) {
            warned.add(prop)
            const msg = `atelier.${prop} leído en modo REAL — debe usar api/* (branch isMock faltante)`
            // eslint-disable-next-line no-console
            console.error(`[REAL LEAK] ${msg}`)
            // eslint-disable-next-line no-console
            console.trace()
            showToast('error', 'Mock leak detectado', msg)
            // auto-clear after 10s so repeated navigations re-warn
            setTimeout(() => warned.delete(prop), 10000)
          }
        }
        return backing
      },
      set(v) {
        if (!isMock.value && !warned.has(`set:${prop}`)) {
          warned.add(`set:${prop}`)
          const msg = `atelier.${prop} escrito en modo REAL — mutación fantasma, usar POST/PUT /api`
          // eslint-disable-next-line no-console
          console.error(`[REAL LEAK] ${msg}`)
          showToast('error', 'Mock leak detectado', msg)
          setTimeout(() => warned.delete(`set:${prop}`), 10000)
        }
        backing = v
        return true
      },
      configurable: true,
      enumerable: true,
    })
  })

  watch(isMock, (v) => {
    if (v) warned.clear()
  })
}
