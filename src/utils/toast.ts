export type ToastSeverity = 'success' | 'info' | 'warn' | 'error' | 'secondary' | 'contrast'

export interface ToastMessage {
  id: string
  severity: ToastSeverity
  summary: string
  detail?: string
  life?: number
}

type ToastListener = (msg: ToastMessage) => void
const listeners: ToastListener[] = []

export function subscribeToToasts(fn: ToastListener): () => void {
  listeners.push(fn)
  return () => {
    const idx = listeners.indexOf(fn)
    if (idx >= 0) listeners.splice(idx, 1)
  }
}

export function showToast(
  severity: ToastSeverity = 'info',
  summary = '',
  detail = '',
  life = 4000
): void {
  const msg: ToastMessage = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    severity,
    summary,
    detail,
    life,
  }
  listeners.forEach((fn) => fn(msg))
}
