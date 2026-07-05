import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getManifest } from '../lib/content'
import { store } from '../lib/store'
import type { Manifest } from '../lib/types'

export default function Home() {
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [picker, setPicker] = useState(false)
  const nav = useNavigate()
  useEffect(() => { getManifest().then(setManifest).catch(console.error) }, [])

  const sessions = store.sessions()
  const returning = sessions.length > 0
  const lastSession = returning ? sessions[sessions.length - 1] : null
  const lastTrack = lastSession && manifest
    ? manifest.tracks.find(t => t.status === 'live' && t.subtopics.includes(lastSession.subtopic)) ?? manifest.tracks[0]
    : null
  const assessed = lastTrack ? lastTrack.subtopics.filter(s => store.mastery(s) !== null).length : 0

  function pickTheme(themeId: string) {
    const live = manifest!.subtopics.filter(s => s.theme === themeId && s.status === 'live')
    setPicker(false)
    if (live.length) nav(`/quiz/${live[0].id}`)
    else nav('/explore')
  }

  return (
    <div className="fade-in">
      <section style={{ textAlign: 'center', padding: '56px 20px 30px', background: 'linear-gradient(180deg, var(--tint) 0%, transparent 85%)' }}>
        <h1 style={{ maxWidth: 640, margin: '0 auto' }}>Where do you actually stand?</h1>
        <p className="muted" style={{ marginTop: 10, maxWidth: 520, marginInline: 'auto' }}>
          Calibrated 2-minute skill checks for data, analytics, and finance professionals. No sign-up.
        </p>
        <button className="btn" style={{ marginTop: 22 }} onClick={() => setPicker(true)}>▶&nbsp; Take a 2-minute check</button>
      </section>

      <div className="container">
        {returning && lastSession && lastTrack ? (
          <div className="card raised" style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <span className="pill">Welcome back</span>
              <h3 style={{ marginTop: 6 }}>{lastTrack.title} track — {assessed} of {lastTrack.subtopics.length} topics assessed</h3>
              <p className="small muted" style={{ marginTop: 4 }}>Pick up where you left off, or try something new below.</p>
            </div>
            <Link className="btn" to={`/tracks/${lastTrack.id}`}>Continue</Link>
          </div>
        ) : (
          <div className="card" style={{ background: 'var(--alt)', display: 'flex', gap: 18, alignItems: 'center', flexWrap: 'wrap' }}>
            <svg width="120" height="74" viewBox="0 0 104 66" style={{ flexShrink: 0 }} aria-hidden>
              <line x1="20" y1="18" x2="52" y2="12" stroke="var(--border)" strokeWidth="2" /><line x1="52" y1="12" x2="84" y2="20" stroke="var(--border)" strokeWidth="2" />
              <line x1="20" y1="18" x2="36" y2="46" stroke="var(--border)" strokeWidth="2" /><line x1="52" y1="12" x2="68" y2="48" stroke="var(--border)" strokeWidth="2" />
              <circle cx="20" cy="18" r="8" fill="var(--good)" /><circle cx="52" cy="12" r="8" fill="var(--good)" />
              <circle cx="84" cy="20" r="8" fill="var(--warn)" /><circle cx="36" cy="46" r="8" fill="var(--bad)" />
              <circle cx="68" cy="48" r="8" fill="var(--card)" stroke="var(--faint)" strokeWidth="2" strokeDasharray="3 2" />
            </svg>
            <div style={{ flex: 1, minWidth: 220 }}>
              <b>Your results in 2 minutes — example</b>
              <p className="small muted" style={{ marginTop: 3 }}>A score with a real percentile, a map of what's strong and shaky, and a study guide to take with you.</p>
            </div>
            <div style={{ textAlign: 'center', paddingRight: 8 }}>
              <div className="display num" style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-dk)' }}>Top 27%</div>
              <div className="small muted">of 412 this month</div>
            </div>
          </div>
        )}

        <p className="muted small" style={{ textAlign: 'center', margin: '26px 0 12px' }}>— or choose your path —</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          <Link to="/explore" className="card lanecard" style={{ textDecoration: 'none', borderTopColor: 'var(--t-teal)' }}>
            <h3>Quick Topics</h3>
            <p className="small muted" style={{ marginTop: 4 }}>5 themes · 2-minute checks</p>
          </Link>
          <Link to="/explore" className="card lanecard" style={{ textDecoration: 'none', borderTopColor: 'var(--t-violet)' }}>
            <h3>Career Tracks</h3>
            <p className="small muted" style={{ marginTop: 4 }}>4 role-based paths, live</p>
          </Link>
          <Link to="/explore" className="card lanecard" style={{ textDecoration: 'none', borderTopColor: 'var(--t-amber)' }}>
            <h3>Certificate Prep</h3>
            <p className="small muted" style={{ marginTop: 4 }}>CFA L1 · Google DA · AWS CP — coming soon</p>
          </Link>
        </div>
      </div>

      <div className="pulsebar" style={{ marginTop: 34 }}>
        <span style={{ color: 'var(--good)', fontWeight: 700 }}>● beta</span>&nbsp; Live market pulse and community stats arrive as the beta grows — every number here will be real, never invented.
      </div>

      {picker && manifest && (
        <>
          <div className="overlay" onClick={() => setPicker(false)} />
          <div className="modal fade-in" role="dialog" aria-label="Pick your theme">
            <h2 style={{ textAlign: 'center' }}>What's your world?</h2>
            <p className="small muted" style={{ textAlign: 'center', margin: '6px 0 14px' }}>
              We'll start you with the right check — 6 questions, about 2 minutes, untimed.
            </p>
            {manifest.themes.map(t => {
              const hasLive = manifest.subtopics.some(s => s.theme === t.id && s.status === 'live')
              return (
                <button key={t.id} className="opt" style={{ justifyContent: 'center', fontWeight: 600 }}
                  disabled={!hasLive} onClick={() => pickTheme(t.id)}>
                  <i className="themedot" style={{ background: t.color }} />
                  {t.title}{!hasLive && <span className="pill gray">soon</span>}
                </button>
              )
            })}
            <p style={{ textAlign: 'center', marginTop: 8 }}>
              <Link className="small muted" to="/explore" onClick={() => setPicker(false)}>or browse all topics →</Link>
            </p>
          </div>
        </>
      )}
    </div>
  )
}
