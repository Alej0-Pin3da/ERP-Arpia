/**
 * useMode — REAL-only mode composable.
 *
 * The frontend no longer supports the in-memory mock backend: every data
 * call goes to FastAPI + Postgres. This composable keeps its historical
 * export shape (`mode` + `isMock`, plus `liveMode`/`liveChecked`/`refresh`/
 * `envMode`) so existing callers compile untouched, but it always resolves
 * to REAL — there are no probe failure paths.
 */
import { ref, computed } from 'vue'

export type ApiMode = 'MOCK' | 'REAL'

function envMode(): ApiMode {
  return 'REAL'
}

export function useMode() {
  const liveMode = ref<ApiMode>('REAL')
  const liveChecked = ref(true)

  async function refresh(): Promise<ApiMode> {
    return mode.value
  }

  const mode = computed<ApiMode>(() => 'REAL')
  const isMock = computed(() => false)

  return { mode, isMock, liveMode, liveChecked, refresh, envMode }
}
