import { afterEach } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

// Unmount every mounted component after each test to avoid leaks between specs.
enableAutoUnmount(afterEach)
