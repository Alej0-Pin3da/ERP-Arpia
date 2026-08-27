/**
 * useMode — determines whether the frontend should use mock (Pinia) or real API.
 *
 * Priority:
 * 1) Live probe GET /api/__mode -> { mode: 'mock' | 'real' } (source of truth, reflects server USE_MOCK/proxy)
 * 2) Fallback to import.meta.env.VITE_USE_MOCK (true => mock, otherwise real)
 *
 * ApiModeBadge already implements the same logic inline; this composable
 * centralizes it for adapters (useClientes / useVentas) and exposes isMock
 * as a computed ref.
 */
import { ref, computed, onMounted } from 'vue'

export type ApiMode = 'MOCK' | 'REAL'

function envMode(): ApiMode {
  const raw = String(import.meta.env.VITE_USE_MOCK ?? '').trim().toLowerCase()
  if (raw === 'true') return 'MOCK'
  if (raw === 'false') return 'REAL'
  // Legacy heuristic: external VITE_API_BASE_URL means REAL (mirrors ApiModeBadge)
  const base = String((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '').trim()
  if (base && !base.startsWith('/api')) {
    const lower = base.toLowerCase()
    if (lower.includes('http') || lower.includes(':8000') || lower.includes(':5433') || lower.includes('backend')) {
      return 'REAL'
    }
  }
  // V4 data-first default: REAL. Mock is opt-in via VITE_USE_MOCK=true or the
  // live /api/__mode probe reporting 'mock'. This is what makes real Postgres
  // data show even when VITE_USE_MOCK is unset (e.g. npm run dev:all).
  return 'REAL'
}

export function useMode() {
  const liveMode = ref<ApiMode | null>(null)
  const liveChecked = ref(false)

  async function refresh(): Promise<ApiMode> {
    try {
      const res = await fetch('/api/__mode', { headers: { Accept: 'application/json' } })
      if (res.ok) {
        const data = (await res.json()) as { mode?: string }
        if (data.mode === 'real') liveMode.value = 'REAL'
        else if (data.mode === 'mock') liveMode.value = 'MOCK'
      }
    } catch {
      // keep fallback
    } finally {
      liveChecked.value = true
    }
    return mode.value
  }

  onMounted(() => {
    void refresh()
  })

  const mode = computed<ApiMode>(() => liveMode.value ?? envMode())
  const isMock = computed(() => mode.value === 'MOCK')

  return { mode, isMock, liveMode, liveChecked, refresh, envMode }
}
