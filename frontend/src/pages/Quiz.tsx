import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { warmBackend } from '../lib/api'
import { getManifest, getSubtopic } from '../lib/content'
import { drawSet, placementItem, routePlacement } from '../lib/elo'
import { store } from '../lib/store'
import type { AnswerRecord, Item, SubtopicContent } from '../lib/types'

type Phase = 'start' | 'placement' | 'quiz' | 'reveal'
type Variant = 'easy' | 'standard' | 'hard'
const KEYS = ['A', 'B', 'C', 'D']

export default function Quiz() {
  const { subtopicId = '' } = useParams()
  const nav = useNavigate()
  const [content, setContent] = useState<SubtopicContent | null>(null)
  const [title, setTitle] = useState(subtopicId)
  const [error, setError] = useState(false)
  const [phase, setPhase] = useState<Phase>('start')
  const [variant, setVariant] = useState<Variant | null>(null)
  const [queue, setQueue] = useState<Item[]>([])
  const [idx, setIdx] = useState(0)
  const [picked, setPicked] = useState<number | null>(null)
  const [answers, setAnswers] = useState<AnswerRecord[]>([])
  const startedAt = useRef(Date.now())

  useEffect(() => {
    warmBackend()  // pre-warm the Space so the percentile call isn't a cold start
    getSubtopic(subtopicId).then(setContent).catch(() => setError(true))
    getManifest().then(m => {
      const meta = m.subtopics.find(s => s.id === subtopicId)
      if (meta) setTitle(meta.title)
    }).catch(() => {})
  }, [subtopicId])

  const placement = useMemo(() => content ? placementItem(content.items) : null, [content])
  const current: Item | null = phase === 'placement' ? placement : (queue[idx] ?? null)

  function begin(v?: Variant) {
    if (!content) return
    if (v) { startQuiz(v) } else { setPhase('placement'); startedAt.current = Date.now() }
  }

  function startQuiz(v: Variant, excludePlacement?: string) {
    if (!content) return
    store.setPlacement(subtopicId, v)
    setVariant(v)
    setQueue(drawSet(content.items, v, store.seenItems(subtopicId), excludePlacement))
    setIdx(0); setPicked(null); setAnswers([])
    setPhase('quiz'); startedAt.current = Date.now()
  }

  function answer(i: number) {
    if (picked !== null || !current) return
    const ms = Date.now() - startedAt.current
    setPicked(i)
    if (phase === 'placement') {
      const v = routePlacement(i === current.answer, ms)
      // brief feedback, then route into the real set
      setTimeout(() => { setPicked(null); startQuiz(v, current.id) }, 1600)
      return
    }
    setAnswers(a => [...a, { itemId: current.id, concept: current.concept, correct: i === current.answer, ms, p: current.difficulty_prior }])
  }

  function next() {
    if (idx + 1 < queue.length) {
      setIdx(idx + 1); setPicked(null); startedAt.current = Date.now()
    } else {
      setPhase('reveal')
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
      const sess = store.addSession(subtopicId, variant ?? 'standard', answers)
      setTimeout(() => nav(`/results/${sess.id}`), reduced ? 0 : 850)
    }
  }

  // keyboard: A-D answer, Enter/-> next
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (phase !== 'quiz' && phase !== 'placement') return
      const k = e.key.toUpperCase()
      const ki = KEYS.indexOf(k)
      if (ki >= 0 && picked === null) answer(ki)
      if ((e.key === 'Enter' || e.key === 'ArrowRight') && picked !== null && phase === 'quiz') next()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  if (error) return (
    <div className="container fade-in" style={{ padding: '48px 20px', textAlign: 'center' }}>
      <h2>This check isn't ready yet</h2>
      <p className="muted" style={{ marginTop: 8 }}>Its questions are still being reviewed. Pick another topic to start with.</p>
      <Link className="btn" style={{ marginTop: 18 }} to="/explore">Browse topics</Link>
    </div>
  )
  if (!content) return <div className="container" style={{ padding: 48 }}><p className="muted">Loading…</p></div>

  if (phase === 'start') return (
    <div className="container fade-in" style={{ maxWidth: 560, padding: '48px 20px' }}>
      <div className="card raised" style={{ textAlign: 'center', padding: 28 }}>
        <span className="pill">{title}</span>
        <h2 style={{ marginTop: 12 }}>Ready when you are</h2>
        <p className="muted" style={{ marginTop: 8 }}>6 questions · about 2 minutes · untimed</p>
        <p className="small muted" style={{ marginTop: 6 }}>One quick question first sets the right difficulty. Right or wrong, you'll learn something on every answer.</p>
        <button className="btn" style={{ marginTop: 18 }} onClick={() => begin()}>Start</button>
        <div style={{ marginTop: 10 }}>
          <button className="textlink small" onClick={() => begin('easy')}>skip — start easier</button>
          <button className="textlink small" onClick={() => begin('hard')}>skip — start harder</button>
        </div>
      </div>
    </div>
  )

  if (phase === 'reveal') return (
    <div className="reveal fade-in">
      <div className="display" style={{ fontSize: '1.3rem', fontWeight: 700 }}>Placing your result…</div>
      <div className="track" style={{ width: 180 }}><div className="fill" style={{ width: '80%' }} /></div>
      <p className="small muted">computed from your answers — never invented</p>
    </div>
  )

  const isPlacement = phase === 'placement'
  const qNum = isPlacement ? 0 : idx + 1
  return (
    <div className="container fade-in" style={{ maxWidth: 640, padding: '28px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span className="pill gray">{title}</span>
        <span className="small muted">{isPlacement ? 'Difficulty check' : `Question ${qNum} of ${queue.length}`}</span>
      </div>
      <div className="track" style={{ marginBottom: 18 }}>
        <div className="fill" style={{ width: `${(qNum / 7) * 100}%` }} />
      </div>
      {current && (
        <div key={current.id} className="fade-in">
          <h3 style={{ lineHeight: 1.45 }}>{current.stem}</h3>
          <div style={{ marginTop: 10 }}>
            {current.options.map((o, i) => {
              let cls = 'opt'
              if (picked !== null) {
                if (i === current.answer) cls += ' right'
                else if (i === picked) cls += ' wrong'
                else cls += ' dim'
              }
              return (
                <button key={i} className={cls} disabled={picked !== null} onClick={() => answer(i)}>
                  <span className="key">{KEYS[i]}</span>{o}
                  {picked !== null && i === current.answer && <span style={{ marginLeft: 'auto', color: 'var(--good)', fontWeight: 700 }}>✓</span>}
                </button>
              )
            })}
          </div>
          {picked !== null && !isPlacement && (
            <div className="explain fade-in">
              <b>{picked === current.answer ? 'Right.' : 'Not quite.'}</b> {current.explanation}
              <div className="src">Source: {current.grounding.source} — {current.grounding.note}</div>
            </div>
          )}
          {picked !== null && isPlacement && (
            <p className="small muted fade-in" style={{ marginTop: 12 }}>Setting your level…</p>
          )}
          {picked !== null && !isPlacement && (
            <div style={{ textAlign: 'right', marginTop: 14 }}>
              <button className="btn" onClick={next}>{idx + 1 < queue.length ? 'Next question →' : 'See my results →'}</button>
            </div>
          )}
          {picked === null && (
            <p className="small" style={{ color: 'var(--faint)', marginTop: 12 }}>Press A–D to answer · untimed, your pace is noted</p>
          )}
        </div>
      )}
    </div>
  )
}
