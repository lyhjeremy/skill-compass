import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getManifest } from '../lib/content'
import { store } from '../lib/store'
import type { Manifest } from '../lib/types'

export default function Explore() {
  const [manifest, setManifest] = useState<Manifest | null>(null)
  useEffect(() => { getManifest().then(setManifest).catch(console.error) }, [])
  if (!manifest) return <div className="container" style={{ padding: 48 }}><p className="muted">Loading…</p></div>

  return (
    <div className="container fade-in" style={{ padding: '32px 20px' }}>
      <h1 style={{ fontSize: '1.8rem' }}>Explore</h1>
      <p className="muted" style={{ marginTop: 4 }}>Every check: 6 questions, about 2 minutes, untimed.</p>

      <h2 style={{ marginTop: 28 }}>Quick topics</h2>
      {manifest.themes.map(t => {
        const subs = manifest.subtopics.filter(s => s.theme === t.id)
        if (!subs.length) return (
          <div key={t.id} className="card" style={{ marginTop: 12, opacity: .7 }}>
            <b><i className="themedot" style={{ background: t.color, marginRight: 8 }} />{t.title}</b>
            <span className="pill gray" style={{ marginLeft: 10 }}>coming soon</span>
          </div>
        )
        return (
          <div key={t.id} className="card" style={{ marginTop: 12 }}>
            <b><i className="themedot" style={{ background: t.color, marginRight: 8 }} />{t.title}</b>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
              {subs.map(s => {
                const mastery = store.mastery(s.id)
                return s.status === 'live' ? (
                  <Link key={s.id} to={`/quiz/${s.id}`} className="btn ghost" style={{ padding: '8px 18px', fontSize: '.9rem' }}>
                    {s.title}{mastery !== null && <span className="pill green num">{mastery}%</span>}
                  </Link>
                ) : (
                  <span key={s.id} className="pill gray" style={{ padding: '8px 18px' }}>{s.title} · soon</span>
                )
              })}
            </div>
          </div>
        )
      })}

      <h2 style={{ marginTop: 32 }}>Career tracks</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 12, marginTop: 12 }}>
        {manifest.tracks.map(t => t.status === 'live' ? (
          <Link key={t.id} className="card lanecard" style={{ textDecoration: 'none', borderTopColor: 'var(--t-violet)' }} to={`/tracks/${t.id}`}>
            <h3>{t.title}</h3><p className="small muted" style={{ marginTop: 4 }}>{t.blurb}</p>
          </Link>
        ) : (
          <div key={t.id} className="card" style={{ opacity: .7 }}>
            <h3>{t.title} <span className="pill gray">soon</span></h3>
            <p className="small muted" style={{ marginTop: 4 }}>{t.blurb}</p>
          </div>
        ))}
      </div>

      <h2 style={{ marginTop: 32 }}>Certificate prep</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 12, marginTop: 12 }}>
        {manifest.certs.map(c => (
          <div key={c.id} className="card" style={{ opacity: .7 }}>
            <h3>{c.title} <span className="pill gray">soon</span></h3>
            <p className="small muted" style={{ marginTop: 4 }}>{c.blurb}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
