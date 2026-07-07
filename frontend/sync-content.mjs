// Rebuilds the manifest from the catalog + whatever content exists, then copies
// content/ JSON into public/content so Vite serves it.
import { cpSync, mkdirSync, existsSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const src = join(here, '..', 'content')
try {
  execFileSync('python3', [join(here, '..', 'scripts', 'build_manifest.py')], { stdio: 'inherit' })
} catch {
  console.warn('build_manifest.py failed or python3 missing; using existing manifest.json')
}
const dst = join(here, 'public', 'content')
mkdirSync(dst, { recursive: true })
cpSync(join(src, 'manifest.json'), join(dst, 'manifest.json'))
const subs = join(src, 'subtopics')
if (existsSync(subs)) cpSync(subs, join(dst, 'subtopics'), { recursive: true })
console.log('content synced -> public/content')
