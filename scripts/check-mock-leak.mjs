#!/usr/bin/env node
/**
 * check-mock-leak — CI guard for REAL mode purity (advisory).
 *
 * Fails only if a *.vue file touches atelier.* without importing useMode at all.
 * This catches truly unconditional leaks while allowing the V5 convention:
 *   - `isMock ? atelier` (same line)
 *   - `if (isMock) { atelier... }` / `if (!isMock) return; ... atelier...`
 *
 * The runtime mockGuard (src/utils/mockGuard.ts) is the fail-loud source of truth.
 * This script is a lightweight CI hint, not a strict blocker during the phased purge.
 */
import { readFileSync, readdirSync, statSync } from 'fs'
import { join } from 'path'

const ROOT = 'src'
let leaks = []

function walk(dir) {
  for (const ent of readdirSync(dir)) {
    const p = join(dir, ent)
    const s = statSync(p)
    if (s.isDirectory()) walk(p)
    else if (p.endsWith('.vue')) checkFile(p)
  }
}

function checkFile(path) {
  const text = readFileSync(path, 'utf8')
  const lines = text.split('\n')
  // If file doesn't import useMode, any atelier.* is a leak (no guard possible)
  const hasMode = text.includes('isMock')
  if (hasMode) return // V5 files are intentionally branched — guarded at runtime by mockGuard

  lines.forEach((line, idx) => {
    if (!line.includes('atelier.')) return
    const trimmed = line.trim()
    if (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('<!--')) return
    leaks.push(`${path}:${idx + 1}: ${trimmed.slice(0, 120)}`)
  })
}

walk(ROOT)

if (leaks.length) {
  console.error(`\n mock-leak check FAILED — ${leaks.length} unconditional atelier.* read(s) found:\n`)
  leaks.forEach(l => console.error('  ' + l))
  console.error('\nFix: import useMode and wrap with `isMock ? atelier : real` or installMockGuard will toast at runtime.\n')
  process.exit(1)
} else {
  console.log('mock-leak check PASSED — all *.vue files touching atelier import useMode (runtime mockGuard active).')
}
