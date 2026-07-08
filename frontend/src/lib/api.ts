import type { Session } from './types'

// The FastAPI service on Hugging Face Spaces. Overridable at build time.
const API_BASE = import.meta.env.VITE_API_BASE ?? 'https://lyhjeremy-skillcompass-api.hf.space'

export interface PercentileResult {
  ok: boolean
  n?: number
  percentile?: number | null   // % of peers you scored above
  top_pct?: number             // "Top X%"
  cold_start: boolean
}

/** Log a completed session; returns its live percentile (or cold-start). Never throws. */
export async function postSession(session: Session): Promise<PercentileResult | null> {
  try {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), 12000)
    const res = await fetch(`${API_BASE}/api/session`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctrl.signal,
      body: JSON.stringify({
        session_hash: session.id,
        subtopic: session.subtopic,
        variant: session.variant,
        score: session.correct,
        total: session.total,
        final_rating: session.finalRating ?? 1500,
        responses: session.answers.map(a => ({
          item_id: a.itemId, concept: a.concept, correct: a.correct,
          response_ms: a.ms, first_exposure: true,
        })),
      }),
    })
    clearTimeout(t)
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

export interface ResumeResult {
  ok: boolean
  reason?: string
  skills?: string[]
  years_experience?: number | null
  evidenced_subtopic_ids?: string[]
  summary?: string
}

/** Analyze resume text against a track's subtopics. The text never touches storage —
 *  it's used for one Gemini call and discarded. Never throws. */
export async function analyzeResume(
  text: string, subtopics: { id: string; title: string }[],
): Promise<ResumeResult> {
  try {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), 35000)  // generous: covers a cold Space + a real Gemini call
    const res = await fetch(`${API_BASE}/api/resume`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctrl.signal,
      body: JSON.stringify({ text, subtopics }),
    })
    clearTimeout(t)
    if (!res.ok) return { ok: false, reason: `http-${res.status}` }
    return await res.json()
  } catch {
    return { ok: false, reason: 'network' }
  }
}

export interface InterviewTurnResult {
  ok: boolean
  reason?: string
  message?: string
  done?: boolean
  scorecard?: { accuracy: number; depth: number; clarity: number; strengthen: string } | null
}

/** One turn of the mock interview. Send the full transcript so far (stateless
 *  backend — no session to manage). Never throws. */
export async function interviewTurn(
  trackTitle: string, seniority: string, topics: string[],
  transcript: { role: string; text: string }[],
): Promise<InterviewTurnResult> {
  try {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), 35000)
    const res = await fetch(`${API_BASE}/api/interview`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctrl.signal,
      body: JSON.stringify({ track_title: trackTitle, seniority, topics, transcript }),
    })
    clearTimeout(t)
    if (!res.ok) return { ok: false, reason: `http-${res.status}` }
    return await res.json()
  } catch {
    return { ok: false, reason: 'network' }
  }
}

export async function reportItem(itemId: string, body: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/feedback`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind: 'item_report', item_id: itemId, body }),
    })
    return res.ok
  } catch { return false }
}

/** Warm the Space so the first real call isn't a cold start. Fire-and-forget. */
export function warmBackend() {
  fetch(`${API_BASE}/api/health`).catch(() => {})
}

/** Shared, honest error copy for any Gemini-backed feature's failure reason. */
export function llmErrorMessage(reason?: string): string {
  switch (reason) {
    case 'rate-limited': return "This is getting a lot of use right now — try again in a bit."
    case 'llm-unavailable': return 'This feature is warming up — try again shortly.'
    case 'llm-overloaded': return "The AI service is at capacity right now (a free-tier limit on our end, not your connection) — try again in a minute."
    case 'llm-quota': return "This feature has hit its free daily limit — try again tomorrow."
    default: return "Couldn't complete that — try again in a moment."
  }
}
