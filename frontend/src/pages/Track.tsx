import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getManifest } from '../lib/content'
import { store } from '../lib/store'
import type { Manifest } from '../lib/types'

export default function Track() {
  const { trackId = '' } = useParams()
  const [manifest, setManifest] = useState<Manifest | null>(null)
  useEffect(() => { getManifest().then(setManifest).catch(console.error) }, [])
  if (!manifest) return <div className="container" style={{ padding: 48 }}><p className="muted">Loading…</p></div>

  const track = manifest.tracks.find(t => t.id === trackId)
  if (!track || track.status !== 'live') return (
    <div className="container" style={{ padding: 48, textAlign: 'center' }}>
      <h2>This track is coming soon</h2>
      <Link className="btn" style={{ marginTop: 16 }} to="/explore">Browse what's live</Link>
    </div>
  )

  const subs = track.subtopics.map(id => manifest.subtopics.find(s => s.id === id)!).filter(Boolean)
  const masteries = subs.map(s => ({ s, m: store.mastery(s.id) }))
  const assessed = masteries.filter(x => x.m !== null).length
  const overall = assessed ? Math.round(masteries.reduce((t, x) => t + (x.m ?? 0), 0) / assessed) : null

  return (
    <div className="container fade-in" style={{ maxWidth: 720, padding: '32px 20px' }}>
      <span className="pill">Career track</span>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
        <h1 style={{ fontSize: '1.9rem', marginTop: 6 }}>{track.title}</h1>
        <span className="small muted num">{assessed} of {subs.length} topics assessed{overall !== null ? ` · overall ${overall}%` : ''}</span>
      </div>
      <p className="muted" style={{ marginTop: 4 }}>{track.blurb}</p>

      <div style={{ marginTop: 20 }}>
        {masteries.map(({ s, m }) => (
          <div key={s.id} className="card" style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 10, padding: '14px 18px' }}>
            <div style={{ flex: 1, minWidth: 140 }}>
              <b>{s.title}</b>
              <div className="track thin" style={{ marginTop: 8, height: 6 }}>
                {m !== null && <div className={`fill ${m >= 70 ? 'good' : m >= 50 ? 'warn' : 'bad'}`} style={{ width: `${m}%` }} />}
              </div>
            </div>
            <span className="small muted num" style={{ width: 44, textAlign: 'right' }}>{m !== null ? `${m}%` : '—'}</span>
            {s.status === 'live'
              ? <Link className="btn ghost" style={{ padding: '8px 18px', fontSize: '.9rem' }} to={`/quiz/${s.id}`}>{m !== null ? 'Retake' : 'Start'}</Link>
              : <span className="pill gray">soon</span>}
          </div>
        ))}
      </div>

      <div className="card" style={{ marginTop: 18, background: 'var(--tint)', border: '1px solid var(--accent)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <b>🎤 Mock interview capstone</b>
          <p className="small" style={{ marginTop: 3, color: 'var(--accent-dk)' }}>
            Unlocks when all {subs.length} topics are assessed — a 6–8 turn interview at your demonstrated level. Coming later in the beta.
          </p>
        </div>
        <span className="pill num" style={{ background: 'var(--card)' }}>{assessed}/{subs.length}</span>
      </div>
      <p className="small muted" style={{ marginTop: 14 }}>
        The live market panel (top skills in this month's postings, salary context) and your gap report arrive in the next beta phase.
      </p>
    </div>
  )
}
