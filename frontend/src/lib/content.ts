import type { Manifest, SubtopicContent } from './types'

const BASE = import.meta.env.BASE_URL + 'content/'
let manifestCache: Manifest | null = null
const subCache = new Map<string, SubtopicContent>()

export async function getManifest(): Promise<Manifest> {
  if (!manifestCache) {
    const r = await fetch(BASE + 'manifest.json')
    if (!r.ok) throw new Error('manifest fetch failed')
    manifestCache = await r.json()
  }
  return manifestCache!
}

export async function getSubtopic(id: string): Promise<SubtopicContent> {
  if (!subCache.has(id)) {
    const r = await fetch(`${BASE}subtopics/${id}.json`)
    if (!r.ok) throw new Error(`subtopic ${id} fetch failed`)
    subCache.set(id, await r.json())
  }
  return subCache.get(id)!
}
