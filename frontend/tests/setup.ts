import { afterEach } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

// Element Plus el-table measures its wrapper with ResizeObserver, which jsdom
// does not implement — without it tables never render their body (or empty
// slot). No-op polyfill keeps table layout code running in tests.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
if (!('ResizeObserver' in globalThis)) {
  ;(globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = ResizeObserverStub
}

// Unmount every mounted component after each test to avoid leaks between specs.
enableAutoUnmount(afterEach)
