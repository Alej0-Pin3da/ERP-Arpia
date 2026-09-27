// V4 Eje 3.3 foundation: "Modo Feria" offline queue for sales.
// localStorage-backed with idempotency keys; sync is idempotent by key.
// Kept dependency-free on purpose: no IndexedDB/ServiceWorker yet.

export interface QueuedSale {
  key: string
  payload: Record<string, unknown>
  queuedAt: string
}

const STORAGE_KEY = 'arpia:offline-queue:v1'

function loadStorage(): Storage | null {
  try {
    if (typeof localStorage === 'undefined') return null
    return localStorage
  } catch {
    return null
  }
}

export function makeKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `k-${Date.now()}-${Math.floor(Math.random() * 1e9)}`
}

export function readQueue(): QueuedSale[] {
  const store = loadStorage()
  if (!store) return []
  try {
    const raw = store.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeQueue(items: QueuedSale[]): void {
  loadStorage()?.setItem(STORAGE_KEY, JSON.stringify(items))
}

export function enqueueSale(payload: Record<string, unknown>, key: string = makeKey()): QueuedSale {
  const items = readQueue()
  if (items.some((i) => i.key === key)) return items.find((i) => i.key === key)!
  const entry: QueuedSale = { key, payload, queuedAt: new Date().toISOString() }
  writeQueue([...items, entry])
  return entry
}

export function dequeueSale(key: string): void {
  writeQueue(readQueue().filter((i) => i.key !== key))
}

export function clearQueue(): void {
  writeQueue([])
}
