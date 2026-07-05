import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getManifest } from '../lib/content'
import { store } from '../lib/store'
import type { Manifest } from '../lib/types'

export default function Progress() {
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [, force] = useState(0)
  useEffect(() => { getManifest().then(setManifest).catch(console.error) }, [])
  const sessions = [...store.sessions()].reverse()
  const title = (id: string) => manifest?.subtopics.find(s => s.id === id)?.title ?? id

  function exportData() {
    const blob = new Blob([store.exportJson()], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'skillcompass-data.json'
    a.click()
    URL.revokeObjectURL(a.href)
  }
  function clearAll() {
    if (confirm('Erase everything SkillCompass has stored on this device? This cannot be undone.')) {
      store.clearAll(); force(x => x + 1)
    }
  }

  return (
    <div className="container fade-in" style={{ maxWidth: 720, padding: '32px 20px' }}>
      <h1 style={{ fontSize: '1.8rem' }}>Your progress</h1>
      <p className="muted small" style={{ marginTop: 4 }}>
        Everything below lives only in this browser — no account, no server copy. Export it or erase it any time.
      </p>

      {sessions.length === 0 ? (
        <div className="card" style={{ marginTop: 20, textAlign: 'center', padding: 32 }}>
          <h3>Nothing here yet</h3>
          <p className="muted small" style={{ marginTop: 6 }}>Take your first 2-minute check and your history starts here.</p>
          <Link className="btn" style={{ marginTop: 16 }} to="/">Take a check</Link>
        </div>
      ) : (
        <>
          <div className="statgrid" style={{ marginTop: 18 }}>
            <div className="tile"><div className="n num">{sessions.length}</div><div className="t">checks completed</div></div>
            <div className="tile"><div className="n num">{new Set(sessions.map(s => s.subtopic)).size}</div><div className="t">topics attempted</div></div>
            <div className="tile"><div className="n num">{Math.round(sessions.reduce((t, s) => t + s.correct / s.total, 0) / sessions.length * 100)}%</div><div className="t">average score</div></div>
          </div>
          <h3 style={{ marginTop: 24 }}>History</h3>
          {sessions.map(s => (
            <div key={s.id} className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 10, padding: '12px 16px' }}>
              <div style={{ flex: 1 }}>
                <b>{title(s.subtopic)}</b>
                <div className="small muted">{new Date(s.ts).toLocaleString()} · {s.variant} set</div>
              </div>
              <span className="num" style={{ fontWeight: 700 }}>{s.correct}/{s.total}</span>
              <Link className="textlink small" to={`/results/${s.id}`}>view</Link>
            </div>
          ))}
        </>
      )}

      <div style={{ display: 'flex', gap: 12, marginTop: 26, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={exportData}>Export my data</button>
        <button className="btn subtle" onClick={clearAll}>Clear everything</button>
      </div>
    </div>
  )
}
