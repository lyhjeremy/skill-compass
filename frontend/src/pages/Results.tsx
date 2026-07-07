import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { KnowledgeMap } from '../components/KnowledgeMap'
import { postSession } from '../lib/api'
import { getManifest, getSubtopic } from '../lib/content'
import { composeDiagnosis } from '../lib/diagnosis'
import { store } from '../lib/store'
import type { SubtopicContent } from '../lib/types'

type Perc = { topPct?: number; n?: number; cold: boolean }

export default function Results() {
  const { sessionId = '' } = useParams()
  const session = store.session(sessionId)
  const [content, setContent] = useState<SubtopicContent | null>(null)
  const [title, setTitle] = useState('')
  const [trackId, setTrackId] = useState('data-analyst')
  const [posting, setPosting] = useState(false)
  const [perc, setPerc] = useState<Perc | null>(
    session?.posted ? { topPct: session.topPct, n: session.nPeers, cold: session.percentile == null } : null)
  const postedRef = useRef(false)

  useEffect(() => {
    if (!session) return
    getSubtopic(session.subtopic).then(setContent).catch(console.error)
    getManifest().then(m => {
      setTitle(m.subtopics.find(s => s.id === session.subtopic)?.title ?? session.subtopic)
      const t = m.tracks.find(t => t.status !== 'soon' && t.subtopics.includes(session.subtopic))
      if (t) setTrackId(t.id)
    }).catch(() => {})

    // Log the session once and pull back its live percentile (Phase 2).
    if (!session.posted && !postedRef.current) {
      postedRef.current = true
      setPosting(true)
      postSession(session).then(r => {
        if (r && r.ok) {
          store.patchSession(session.id, {
            posted: true, percentile: r.percentile ?? null, topPct: r.top_pct, nPeers: r.n })
          setPerc({ topPct: r.top_pct, n: r.n, cold: r.cold_start })
        } else {
          setPerc(null)  // backend off/unreachable -> stays "early data", retries next visit
        }
        setPosting(false)
      })
    }
  }, [sessionId])

  if (!session) return (
    <div className="container" style={{ padding: 48, textAlign: 'center' }}>
      <h2>No result found on this device</h2>
      <p className="muted small" style={{ marginTop: 8 }}>Results live only in your browser — this link may be from another device.</p>
      <Link className="btn" style={{ marginTop: 16 }} to="/">Take a check</Link>
    </div>
  )
  if (!content) return <div className="container" style={{ padding: 48 }}><p className="muted">Loading…</p></div>

  const states = store.conceptStates(session.subtopic, content)
  const { text, nextConcept } = composeDiagnosis(session, content, states)
  const attempts = store.sessionsFor(session.subtopic).length
  const missedStems: Record<string, string> = {}
  for (const a of session.answers) if (!a.correct) {
    const item = content.items.find(i => i.id === a.itemId)
    if (item && !missedStems[a.concept]) missedStems[a.concept] = item.stem
  }
  const avgSec = Math.round(session.avgMs / 1000)

  function download() {
    const label = (id: string) => content!.concepts.find(c => c.id === id)?.label ?? id
    const lines = [
      `# Your SkillCompass check — ${title}`, '',
      `Generated ${new Date(session!.ts).toLocaleDateString()} · https://lyhjeremy.github.io/skill-compass/`, '',
      `## Result`, `- Score: **${session!.correct}/${session!.total}** (attempt ${attempts})`,
      `- Average pace: ~${avgSec}s per question`, '',
      `## What this says`, text, '',
      `## Concept map`,
      ...content!.concepts.map(c => `- ${c.label}: **${states[c.id]}** — ${c.definition}`), '',
      `## Keep growing — paste into any AI chat`, '```',
      `You are my tutor. My weak areas in ${title}: ${content!.concepts.filter(c => states[c.id] === 'missed' || states[c.id] === 'shaky').map(c => c.label).join(', ') || '(none — challenge me)'}.`,
      `Quiz me with 5 new practice questions, one at a time, correcting me as we go.`, '```', '',
      nextConcept ? `Next move: ${label(nextConcept.id)}.` : 'Next move: a fresh attempt on new questions.',
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `skillcompass-${session!.subtopic}.md`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <div className="container fade-in" style={{ maxWidth: 720, padding: '32px 20px' }}>
      {/* 1 · score (mobile order: score -> diagnosis -> map -> actions, spec §5.4) */}
      <div className="card raised" style={{ textAlign: 'center', padding: 26 }}>
        <span className="pill">{title}</span>
        <div className="display num" style={{ fontSize: '3rem', fontWeight: 800, marginTop: 8 }}>
          {session.correct}<span style={{ color: 'var(--faint)', fontSize: '1.8rem' }}>/{session.total}</span>
        </div>
        {perc && !perc.cold && perc.topPct != null ? (
          <>
            <div className="display" style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--accent-dk)', marginTop: 2 }}>
              Top {perc.topPct}%
            </div>
            <p className="small muted" style={{ marginTop: 2 }}>of {perc.n} people on this topic in the last 90 days</p>
          </>
        ) : posting ? (
          <p className="small muted" style={{ marginTop: 6 }}>Placing your result…</p>
        ) : (
          <p className="small muted" style={{ marginTop: 6 }}>
            <b style={{ color: 'var(--ink)' }}>Early data</b> — you're one of the first here.
            Live percentiles switch on once this topic has 30+ sessions; your result is saved on this device.
          </p>
        )}
        <p className="small muted" style={{ marginTop: 4 }}>⏱ ~{avgSec}s per question{attempts > 1 ? ` · attempt ${attempts}` : ''}</p>
      </div>

      {/* 2 · diagnosis */}
      <div className="explain" style={{ marginTop: 16, fontSize: '1rem' }}>
        <b>What this says:</b> {text}
      </div>

      {/* 3 · map */}
      <h3 style={{ marginTop: 26 }}>Your knowledge map</h3>
      <p className="small muted" style={{ margin: '4px 0 10px' }}>Tap any concept to see what it is and how to close it.</p>
      <KnowledgeMap content={content} states={states} missedStems={missedStems} retakeTo={`/quiz/${session.subtopic}`} />

      {/* 4 · actions */}
      <div style={{ display: 'flex', gap: 12, marginTop: 26, flexWrap: 'wrap' }}>
        <button className="btn" onClick={download}>↓ Save your study notes</button>
        <Link className="btn ghost" to={`/quiz/${session.subtopic}`}>Take it again</Link>
        <Link className="btn subtle" to={`/tracks/${trackId}`}>Back to your track</Link>
      </div>
      <p className="small muted" style={{ marginTop: 14 }}>
        Shareable result cards and the market gap report arrive later in the beta — <Link to="/methodology">see what's coming</Link>.
      </p>
    </div>
  )
}
