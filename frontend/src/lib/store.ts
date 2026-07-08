import { PLACEMENT_START, itemRating, updateSession as eloUpdate } from './elo'
import type { AnswerRecord, ConceptState, ResumeProfile, Session, SubtopicContent } from './types'

/** All user state lives on-device: localStorage schema sc_v1 (spec §5.14). */
interface StoreShape {
  version: 1
  sessions: Session[]
  placements: Record<string, 'easy' | 'standard' | 'hard'>
  resumes: Record<string, ResumeProfile>  // keyed by trackId
}
const KEY = 'sc_v1'

function load(): StoreShape {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) {
      const s = JSON.parse(raw)
      if (s.version === 1) return { resumes: {}, ...s }  // tolerate pre-resume data
    }
  } catch { /* corrupted -> fresh */ }
  return { version: 1, sessions: [], placements: {}, resumes: {} }
}
function save(s: StoreShape) { localStorage.setItem(KEY, JSON.stringify(s)) }

export const store = {
  all: (): StoreShape => load(),
  sessions: (): Session[] => load().sessions,
  session: (id: string): Session | undefined => load().sessions.find(s => s.id === id),
  sessionsFor: (subtopic: string): Session[] => load().sessions.filter(s => s.subtopic === subtopic),

  addSession(subtopic: string, variant: Session['variant'], answers: AnswerRecord[]): Session {
    const s = load()
    // final session ability: fold the Elo update over answers in order (spec §7)
    let rating: number = PLACEMENT_START[variant]
    for (const a of answers) {
      if (typeof a.p === 'number') rating = eloUpdate(rating, itemRating(a.p), a.correct)
    }
    const sess: Session = {
      id: `s${Date.now().toString(36)}${Math.floor(Math.random() * 1e4).toString(36)}`,
      subtopic, ts: Date.now(), variant,
      correct: answers.filter(a => a.correct).length, total: answers.length,
      answers, avgMs: Math.round(answers.reduce((t, a) => t + a.ms, 0) / Math.max(1, answers.length)),
      finalRating: Math.round(rating),
    }
    s.sessions.push(sess)
    save(s)
    return sess
  },

  /** Patch a stored session (e.g. with the percentile the backend returned). */
  patchSession(id: string, patch: Partial<Session>) {
    const s = load()
    const i = s.sessions.findIndex(x => x.id === id)
    if (i >= 0) { s.sessions[i] = { ...s.sessions[i], ...patch }; save(s) }
  },

  setPlacement(subtopic: string, v: 'easy' | 'standard' | 'hard') {
    const s = load(); s.placements[subtopic] = v; save(s)
  },
  placement: (subtopic: string) => load().placements[subtopic],

  /** ids of items already answered in any session for a subtopic (unseen-first draws) */
  seenItems(subtopic: string): Set<string> {
    const seen = new Set<string>()
    for (const sess of this.sessionsFor(subtopic)) for (const a of sess.answers) seen.add(a.itemId)
    return seen
  },

  /** latest response per item across attempts -> per-concept state (spec §7 retakes) */
  conceptStates(subtopic: string, content: SubtopicContent): Record<string, ConceptState> {
    const latest = new Map<string, boolean>()
    const ordered = this.sessionsFor(subtopic).sort((a, b) => a.ts - b.ts)
    for (const sess of ordered) for (const a of sess.answers) latest.set(a.itemId, a.correct)
    const byConcept = new Map<string, boolean[]>()
    for (const item of content.items) {
      if (latest.has(item.id)) {
        if (!byConcept.has(item.concept)) byConcept.set(item.concept, [])
        byConcept.get(item.concept)!.push(latest.get(item.id)!)
      }
    }
    const out: Record<string, ConceptState> = {}
    for (const c of content.concepts) {
      const results = byConcept.get(c.id)
      if (!results || results.length === 0) out[c.id] = 'untested'
      else if (results.every(Boolean)) out[c.id] = 'strong'
      else if (results.some(Boolean)) out[c.id] = 'shaky'
      else out[c.id] = 'missed'
    }
    return out
  },

  /** 0-100 mastery for a subtopic: share of latest-answered items correct */
  mastery(subtopic: string): number | null {
    const latest = new Map<string, boolean>()
    const ordered = this.sessionsFor(subtopic).sort((a, b) => a.ts - b.ts)
    for (const sess of ordered) for (const a of sess.answers) latest.set(a.itemId, a.correct)
    if (latest.size === 0) return null
    const vals = [...latest.values()]
    return Math.round((vals.filter(Boolean).length / vals.length) * 100)
  },

  resume: (trackId: string): ResumeProfile | undefined => load().resumes[trackId],
  setResume(profile: ResumeProfile) {
    const s = load(); s.resumes[profile.trackId] = profile; save(s)
  },
  clearResume(trackId: string) {
    const s = load(); delete s.resumes[trackId]; save(s)
  },

  exportJson(): string { return JSON.stringify(load(), null, 2) },
  clearAll() { localStorage.removeItem(KEY) },
}
