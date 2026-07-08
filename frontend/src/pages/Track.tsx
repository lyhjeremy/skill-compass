import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { analyzeResume, generateGuide, llmErrorMessage, warmBackend, type GuideSubtopic } from '../lib/api'
import { getManifest, getSubtopic } from '../lib/content'
import { store } from '../lib/store'
import type { Manifest, ResumeProfile, StudyGuide } from '../lib/types'

function renderGuideMarkdown(md: string) {
  const blocks: React.ReactNode[] = []
  let list: string[] = []
  let ordered = false
  const inline = (text: string, key: string) =>
    text.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
      p.startsWith('**') && p.endsWith('**') ? <b key={`${key}-${i}`}>{p.slice(2, -2)}</b> : <span key={`${key}-${i}`}>{p}</span>)
  const flush = (key: string) => {
    if (list.length) {
      const Tag = ordered ? 'ol' : 'ul'
      blocks.push(<Tag key={key} style={{ margin: '6px 0 10px 20px' }}>{list.map((li, i) => <li key={i} style={{ marginBottom: 5 }}>{inline(li, `${key}-${i}`)}</li>)}</Tag>)
      list = []
    }
  }
  md.split('\n').forEach((raw, i) => {
    const t = raw.trim()
    if (t.startsWith('## ')) { flush(`b${i}`); blocks.push(<h3 key={i} style={{ marginTop: 18, fontSize: '1.02rem' }}>{t.slice(3)}</h3>) }
    else if (t.startsWith('# ')) { flush(`b${i}`); blocks.push(<h2 key={i} style={{ marginTop: 4, fontSize: '1.2rem' }}>{t.slice(2)}</h2>) }
    else if (/^\d+\.\s/.test(t)) { if (!list.length) ordered = true; list.push(t.replace(/^\d+\.\s/, '')) }
    else if (t.startsWith('- ') || t.startsWith('* ')) { if (!list.length) ordered = false; list.push(t.slice(2)) }
    else if (t === '') { flush(`b${i}`) }
    else { flush(`b${i}`); blocks.push(<p key={i} style={{ marginTop: 8, lineHeight: 1.55 }}>{inline(t, `p${i}`)}</p>) }
  })
  flush('bend')
  return blocks
}

export default function Track() {
  const { trackId = '' } = useParams()
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [profile, setProfile] = useState<ResumeProfile | undefined>(undefined)
  const [text, setText] = useState('')
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [guide, setGuide] = useState<StudyGuide | undefined>(undefined)
  const [guideBusy, setGuideBusy] = useState(false)
  const [guideError, setGuideError] = useState<string | null>(null)

  useEffect(() => { getManifest().then(setManifest).catch(console.error); warmBackend() }, [])
  useEffect(() => {
    setProfile(store.resume(trackId)); setEditing(false); setError(null)
    setGuide(store.guide(trackId)); setGuideError(null)
  }, [trackId])

  if (!manifest) return <div className="container" style={{ padding: 48 }}><p className="muted">Loading…</p></div>

  const track = manifest.tracks.find(t => t.id === trackId)
  if (!track || track.status === 'soon') return (
    <div className="container" style={{ padding: 48, textAlign: 'center' }}>
      <h2>This track is coming soon</h2>
      <p className="muted small" style={{ marginTop: 8 }}>Its topics are still being written and reviewed.</p>
      <Link className="btn" style={{ marginTop: 16 }} to="/explore">Browse what's live</Link>
    </div>
  )

  const subs = track.subtopics.map(id => manifest.subtopics.find(s => s.id === id)!).filter(Boolean)
  const masteries = subs.map(s => ({ s, m: store.mastery(s.id) }))
  const assessed = masteries.filter(x => x.m !== null).length
  const overall = assessed ? Math.round(masteries.reduce((t, x) => t + (x.m ?? 0), 0) / assessed) : null
  const evidenced = new Set(profile?.evidencedSubtopicIds ?? [])
  const gaps = masteries.filter(x => x.m === null && !evidenced.has(x.s.id) && x.s.status === 'live')

  async function analyze() {
    setError(null)
    if (text.trim().length < 80) {
      setError('Paste a bit more of your resume for an accurate read (a few sentences of experience).')
      return
    }
    setBusy(true)
    const r = await analyzeResume(text.trim(), subs.map(s => ({ id: s.id, title: s.title })))
    setBusy(false)
    if (!r.ok) { setError(llmErrorMessage(r.reason)); return }
    const p: ResumeProfile = {
      trackId, skills: r.skills ?? [], yearsExperience: r.years_experience ?? null,
      evidencedSubtopicIds: r.evidenced_subtopic_ids ?? [], summary: r.summary ?? '', ts: Date.now(),
    }
    store.setResume(p)
    setProfile(p)
    setEditing(false)
    setText('')
  }

  function removeResume() {
    store.clearResume(trackId)
    setProfile(undefined)
    setEditing(false)
  }

  async function buildGuide() {
    setGuideError(null)
    setGuideBusy(true)
    const payload: GuideSubtopic[] = await Promise.all(masteries.map(async ({ s, m }) => {
      if (m === null) return { title: s.title, mastery: null, concepts: [] }
      try {
        const content = await getSubtopic(s.id)
        const states = store.conceptStates(s.id, content)
        return {
          title: s.title, mastery: m,
          concepts: content.concepts.map(c => ({ label: c.label, state: states[c.id] })),
        }
      } catch {
        return { title: s.title, mastery: m, concepts: [] }
      }
    }))
    const r = await generateGuide(track!.title, payload, profile?.summary, store.interview(trackId)?.scorecard.strengthen)
    setGuideBusy(false)
    if (!r.ok || !r.guide_md) { setGuideError(llmErrorMessage(r.reason)); return }
    const g: StudyGuide = { trackId, markdown: r.guide_md, ts: Date.now() }
    store.setGuide(g)
    setGuide(g)
  }

  function downloadGuide() {
    if (!guide) return
    const blob = new Blob([guide.markdown], { type: 'text/markdown' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `skillcompass-study-guide-${trackId}.md`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <div className="container fade-in" style={{ maxWidth: 720, padding: '32px 20px' }}>
      <span className="pill">Career track</span>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
        <h1 style={{ fontSize: '1.9rem', marginTop: 6 }}>{track.title}</h1>
        <span className="small muted num">{assessed} of {subs.length} topics assessed{overall !== null ? ` · overall ${overall}%` : ''}</span>
      </div>
      <p className="muted" style={{ marginTop: 4 }}>{track.blurb}</p>

      {/* Resume gap report */}
      {profile && !editing ? (
        <div className="card" style={{ marginTop: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <b>Your resume, for this track</b>
            <span>
              <button className="textlink small" onClick={() => setEditing(true)}>Redo</button>
              {' · '}
              <button className="textlink small" onClick={removeResume}>Remove</button>
            </span>
          </div>
          {profile.summary && <p className="small" style={{ marginTop: 6 }}>{profile.summary}</p>}
          {profile.yearsExperience != null && (
            <p className="small muted" style={{ marginTop: 2 }}>~{profile.yearsExperience} years of relevant experience</p>
          )}
          {profile.skills.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
              {profile.skills.map(sk => <span key={sk} className="pill gray">{sk}</span>)}
            </div>
          )}
        </div>
      ) : (
        <div className="card" style={{ marginTop: 20, border: '1.5px dashed var(--accent)', background: 'var(--tint)' }}>
          <b>Add your resume <span className="muted" style={{ fontWeight: 400 }}>(optional)</span></b>
          <p className="small muted" style={{ marginTop: 4 }}>
            See which of these topics your experience already covers — paste the text, no file upload needed.
          </p>
          <textarea
            value={text} onChange={e => setText(e.target.value)} rows={6} disabled={busy}
            placeholder="Paste your resume text here…"
            style={{ width: '100%', marginTop: 10, padding: 12, borderRadius: 10, border: '1px solid var(--border)',
                     background: 'var(--card)', color: 'var(--ink)', font: 'inherit', resize: 'vertical' }}
          />
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', background: 'var(--card)', border: '1px solid var(--border)',
                        borderRadius: 8, padding: '8px 10px', marginTop: 8 }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="1.8" style={{ flexShrink: 0 }}>
              <rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
            </svg>
            <p className="small muted">This text is analyzed once and never stored — nothing is saved on our servers; results stay only on this device.</p>
          </div>
          {error && <p className="small" style={{ color: 'var(--bad)', marginTop: 8 }}>{error}</p>}
          <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
            <button className="btn" onClick={analyze} disabled={busy}>{busy ? 'Analyzing…' : 'Analyze my experience →'}</button>
            {profile && <button className="textlink" onClick={() => { setEditing(false); setError(null) }}>Cancel</button>}
          </div>
        </div>
      )}

      {gaps.length > 0 && (
        <div className="card" style={{ marginTop: 14, background: 'var(--alt)' }}>
          <b className="small">Your biggest gaps in this track</b>
          <p className="small muted" style={{ marginTop: 4 }}>
            No quiz or resume evidence yet for: {gaps.map(g => g.s.title).join(', ')}.
          </p>
        </div>
      )}

      <div style={{ marginTop: 20 }}>
        {masteries.map(({ s, m }) => {
          const fromResume = m === null && evidenced.has(s.id)
          return (
            <div key={s.id} className="card" style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 10, padding: '14px 18px' }}>
              <div style={{ flex: 1, minWidth: 140 }}>
                <b>{s.title}</b>
                {m !== null ? (
                  <div className="track thin" style={{ marginTop: 8, height: 6 }}>
                    <div className={`fill ${m >= 70 ? 'good' : m >= 50 ? 'warn' : 'bad'}`} style={{ width: `${m}%` }} />
                  </div>
                ) : fromResume ? (
                  <div style={{ marginTop: 6 }}><span className="pill green">From resume</span></div>
                ) : null}
              </div>
              <span className="small muted num" style={{ width: 44, textAlign: 'right' }}>{m !== null ? `${m}%` : '—'}</span>
              {s.status === 'live'
                ? <Link className="btn ghost" style={{ padding: '8px 18px', fontSize: '.9rem' }} to={`/quiz/${s.id}`}>{m !== null ? 'Retake' : fromResume ? 'Verify' : 'Start'}</Link>
                : <span className="pill gray">soon</span>}
            </div>
          )
        })}
      </div>

      <div className="card" style={{ marginTop: 18, background: 'var(--tint)', border: '1px solid var(--accent)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <b>🎤 Mock interview capstone</b>
          <p className="small" style={{ marginTop: 3, color: 'var(--accent-dk)' }}>
            {track.status === 'live' && assessed === subs.length
              ? 'Unlocked — a 6–8 turn interview at your demonstrated level, with honest feedback.'
              : `Unlocks when all ${subs.length} topics are assessed — a 6–8 turn interview at your demonstrated level.`}
          </p>
        </div>
        {track.status === 'live' && assessed === subs.length
          ? <Link className="btn" style={{ padding: '8px 18px', fontSize: '.9rem' }} to={`/interview/${trackId}`}>Start</Link>
          : <span className="pill num" style={{ background: 'var(--card)' }}>{assessed}/{subs.length}</span>}
      </div>

      {assessed > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
            <b>📋 Your personalized study guide</b>
            {guide && (
              <span>
                <button className="textlink small" onClick={buildGuide} disabled={guideBusy}>Regenerate</button>
                {' · '}
                <button className="textlink small" onClick={downloadGuide}>Download .md</button>
              </span>
            )}
          </div>
          {!guide ? (
            <>
              <p className="small muted" style={{ marginTop: 4 }}>
                A short, specific plan built from your real quiz results{profile ? ', your resume,' : ''}{store.interview(trackId) ? ' and your interview feedback' : ''} — where to focus first, what's already solid, and a suggested order.
              </p>
              {guideError && <p className="small" style={{ color: 'var(--bad)', marginTop: 8 }}>{guideError}</p>}
              <button className="btn" style={{ marginTop: 10 }} onClick={buildGuide} disabled={guideBusy}>
                {guideBusy ? 'Writing your guide…' : 'Generate my study guide →'}
              </button>
            </>
          ) : (
            <div style={{ marginTop: 6 }}>
              {guideError && <p className="small" style={{ color: 'var(--bad)', marginBottom: 8 }}>{guideError}</p>}
              {renderGuideMarkdown(guide.markdown)}
            </div>
          )}
        </div>
      )}

      <p className="small muted" style={{ marginTop: 14 }}>
        This gap report compares you against this track's own curriculum. A live job-market panel (top skills in this month's postings, salary context) arrives in a later beta phase.
      </p>
    </div>
  )
}
