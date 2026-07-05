// Copies the repo's content/ JSON into public/content so Vite serves it.
import { cpSync, mkdirSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const src = join(here, '..', 'content')
const dst = join(here, 'public', 'content')
mkdirSync(dst, { recursive: true })
cpSync(join(src, 'manifest.json'), join(dst, 'manifest.json'))
const subs = join(src, 'subtopics')
if (existsSync(subs)) cpSync(subs, join(dst, 'subtopics'), { recursive: true })
console.log('content synced -> public/content')
