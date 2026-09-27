import { beforeEach, describe, expect, it } from 'vitest'
import { clearQueue, dequeueSale, enqueueSale, readQueue } from './offline-queue'

describe('offline-queue (Modo Feria)', () => {
  beforeEach(() => clearQueue())

  it('enqueues and reads back', () => {
    enqueueSale({ total: 100 }, 'k-1')
    expect(readQueue()).toHaveLength(1)
  })

  it('is idempotent by key', () => {
    enqueueSale({ total: 100 }, 'k-1')
    enqueueSale({ total: 999 }, 'k-1')
    const items = readQueue()
    expect(items).toHaveLength(1)
    expect(items[0].payload).toEqual({ total: 100 })
  })

  it('dequeues by key', () => {
    enqueueSale({ total: 1 }, 'k-1')
    enqueueSale({ total: 2 }, 'k-2')
    dequeueSale('k-1')
    expect(readQueue().map((i) => i.key)).toEqual(['k-2'])
  })
})
