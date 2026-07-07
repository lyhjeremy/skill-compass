import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getManifest } from '../lib/content'
import { store } from '../lib/store'
import type { Manifest } from '../lib/types'

const RANK = { live: 0, partial: 1, soon: 2 } as const

export default function Explore() {
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [showAllThemes, setShowAllThemes] = useState(false)
  useEffect(() => { getManifest().then(setManifest).catch(console.error) }, [])

  const themes = useMemo(() => {
    if (!manifest) return []
    return [...manifest.themes].sort((a, b) =>
      RANK[a.status] - RANK[b.status] || Number(!!b.featured) - Number(!!a.featured))
  }, [manifest])
  const tracks = useMemo(() => {
    if (!manifest) return []
    return [...manifest.tracks].sort((a, b) =>
      RANK[a.status] - RANK[b.status] || (b.ready ?? 0) - (a.ready ?? 0))
  }, [manifest])

  if (!manifest) return <div className="container" style={{ padding: 48 }}><p className="muted">Loading…</p></div>

  const liveThemes = themes.filter(t => t.status === 'live')
  const soonThemes = themes.filter(t => t.status === 'soon')
  const liveCount = manifest.subtopics.filter(s => s.status === 'live').length

  return (
    <div className="container fade-in" style={{ padding: '32px 20px' }}>
      <h1 style={{ fontSize: '1.8rem' }}>Explore</h1>
      <p className="muted" style={{ marginTop: 4 }}>
        {liveCount} topics live across {liveThemes.length} fields · {tracks.filter(t => t.status !== 'soon').length} career tracks. Every check: 6 questions, ~2 minutes, untimed.
      </p>

      <h2 style={{ marginTop: 28 }}>Quick topics</h2>
      {liveThemes.map(t => {
        const subs = manifest.subtopics.filter(s => s.theme === t.id)
        const live = subs.filter(s => s.status === 'live')
        const soon = subs.length - live.length
        return (
          <div key={t.id} className="card" style={{ marginTop: 12 }}>
            <b><i className="themedot" style={{ background: t.color, marginRight: 8 }} />{t.title}</b>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 12, alignItems: 'center' }}>
              {live.map(s => {
                const mastery = store.mastery(s.id)
                return (
                  <Link key={s.id} to={`/quiz/${s.id}`} className="btn ghost" style={{ padding: '8px 16px', fontSize: '.9rem' }}>
                    {s.title}{mastery !== null && <span className="pill green num">{mastery}%</span>}
                  </Link>
                )
              })}
              {soon > 0 && <span className="small muted">+{soon} more coming</span>}
            </div>
          </div>
        )
      })}

      {soonThemes.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <button className="textlink small" onClick={() => setShowAllThemes(v => !v)}>
            {showAllThemes ? 'Hide' : `Show ${soonThemes.length} more fields on the way →`}
          </button>
          {showAllThemes && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
              {soonThemes.map(t => (
                <span key={t.id} className="pill gray" style={{ padding: '6px 12px' }}>
                  <i className="themedot" style={{ background: t.color, marginRight: 6, opacity: .6 }} />{t.title}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <h2 style={{ marginTop: 34 }}>Career tracks</h2>
      <p className="small muted" style={{ marginTop: 2 }}>Role-based paths. Start any track with a ready topic and build up as more land.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 12 }}>
        {tracks.map(t => {
          const browsable = t.status !== 'soon'
          const inner = (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 6 }}>
                <h3>{t.title}</h3>
                {t.status === 'live' && <span className="pill green">ready</span>}
                {t.status === 'partial' && <span className="pill num">{t.ready}/{t.total}</span>}
                {t.status === 'soon' && <span className="pill gray">soon</span>}
              </div>
              <p className="small muted" style={{ marginTop: 4 }}>{t.blurb}</p>
            </>
          )
          return browsable
            ? <Link key={t.id} className="card lanecard" style={{ textDecoration: 'none', borderTopColor: 'var(--t-violet)' }} to={`/tracks/${t.id}`}>{inner}</Link>
            : <div key={t.id} className="card" style={{ opacity: .65 }}>{inner}</div>
        })}
      </div>

      <h2 style={{ marginTop: 34 }}>Certificate prep</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 12 }}>
        {manifest.certs.map(c => (
          <div key={c.id} className="card" style={{ opacity: .65 }}>
            <h3>{c.title} <span className="pill gray">soon</span></h3>
            <p className="small muted" style={{ marginTop: 4 }}>{c.blurb}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
