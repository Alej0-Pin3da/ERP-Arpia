/**
 * Toast singleton unit tests (task S0-T4, spec BEH-2 path).
 *
 * The module singleton bridges PrimeVue's ToastService (available only inside
 * a mounted component) to non-component code such as the axios 403
 * interceptor in client.ts. Before the app root registers the instance it
 * must be a safe no-op; after registration it must delegate to the service.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ToastServiceMethods } from 'primevue/toastservice'

// Reset the module between tests so the singleton starts unset every time.
async function freshToastModule() {
  vi.resetModules()
  return await import('@/utils/toast')
}

describe('toast singleton (BEH-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('is a safe no-op before an instance is registered', async () => {
    const { showToast } = await freshToastModule()

    expect(() => showToast('success', 'Guardado', 'Cambios aplicados')).not.toThrow()
  })

  it('delegates severity, summary, detail and default life (3000) to the service', async () => {
    const add = vi.fn()
    const instance = { add } as unknown as ToastServiceMethods
    const { setToastInstance, showToast } = await freshToastModule()

    setToastInstance(instance)
    showToast('error', 'Error de red', 'No se pudo conectar')

    expect(add).toHaveBeenCalledTimes(1)
    expect(add).toHaveBeenCalledWith({
      severity: 'error',
      summary: 'Error de red',
      detail: 'No se pudo conectar',
      life: 3000,
    })
  })

  it('honours an explicit life override', async () => {
    const add = vi.fn()
    const instance = { add } as unknown as ToastServiceMethods
    const { setToastInstance, showToast } = await freshToastModule()

    setToastInstance(instance)
    showToast('info', 'Recordatorio', undefined, 6000)

    expect(add).toHaveBeenCalledWith({
      severity: 'info',
      summary: 'Recordatorio',
      detail: undefined,
      life: 6000,
    })
  })
})