/**
 * ConfirmDialog singleton unit tests (task S4-T1, spec BEH-5).
 *
 * confirmAction() bridges PrimeVue's ConfirmationService — available only
 * inside a mounted component (App.vue captures it in setup) — to component
 * code that previously awaited ElMessageBox.confirm. Before the host
 * registers, confirmAction resolves 'reject': a missing host must never
 * perform the destructive action (BEH-5 path).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ConfirmationOptions } from 'primevue/confirmationoptions'
import type { ConfirmationServiceMethods } from 'primevue/confirmationservice'

// Reset the module between tests so the singleton starts unset every time.
async function freshConfirmModule() {
  vi.resetModules()
  return await import('@/utils/confirm')
}

describe('confirm singleton (BEH-5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('resolves reject before an instance is registered (safe no-op)', async () => {
    const { confirmAction } = await freshConfirmModule()

    await expect(confirmAction({ message: '¿Eliminar el registro?' })).resolves.toBe('reject')
  })

  it('resolves accept when the user confirms, forwarding the options', async () => {
    const require = vi.fn((options: ConfirmationOptions) => options.accept?.())
    const instance = { require, close: vi.fn() } as unknown as ConfirmationServiceMethods
    const { setConfirmInstance, confirmAction } = await freshConfirmModule()

    setConfirmInstance(instance)
    const result = confirmAction({
      message: '¿Eliminar el registro?',
      header: 'Confirmar eliminación',
      acceptLabel: 'Eliminar',
      rejectLabel: 'Cancelar',
    })

    expect(require).toHaveBeenCalledWith(
      expect.objectContaining({
        message: '¿Eliminar el registro?',
        header: 'Confirmar eliminación',
        acceptLabel: 'Eliminar',
        rejectLabel: 'Cancelar',
      }),
    )
    await expect(result).resolves.toBe('accept')
  })

  it('resolves reject when the user cancels', async () => {
    const require = vi.fn((options: ConfirmationOptions) => options.reject?.())
    const instance = { require, close: vi.fn() } as unknown as ConfirmationServiceMethods
    const { setConfirmInstance, confirmAction } = await freshConfirmModule()

    setConfirmInstance(instance)
    await expect(confirmAction({ message: '¿Eliminar el registro?' })).resolves.toBe('reject')
  })
})
