import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getQuota, type QuotaState } from '../lib/api'
import { store } from '../lib/store'

function QuotaMeter() {
  const [quota, setQuota] = useState<QuotaState | null>(null)
  useEffect(() => { getQuota().then(setQuota) }, [])
  if (!quota || !quota.ok || quota.cap == null) return null

  const pct = Math.min(100, Math.round(((quota.used ?? 0) / quota.cap) * 100))
  const low = pct >= 85
  return (
    <div className="card" style={{ marginTop: 14, padding: '14px 18px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.85rem' }}>
        <b>Today's live-AI capacity</b>
        <span className="muted">{quota.used} / {quota.cap} calls</span>
      </div>
      <div className="track thin" style={{ marginTop: 8 }}>
        <div className={`fill ${low ? 'warn' : 'good'}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="small muted" style={{ marginTop: 8 }}>
        The free Gemini tier this runs on caps out around here — self-tracked since the
        backend last restarted, not a literal daily reset. When it's low, cached answers
        still work; new ones may briefly say "at capacity, try again shortly."
      </p>
    </div>
  )
}

export function Dashboard() {
  const local = store.sessions().length
  return (
    <div className="container fade-in" style={{ maxWidth: 720, padding: '32px 20px' }}>
      <h1 style={{ fontSize: '1.8rem' }}>Live dashboard</h1>
      <p className="muted small" style={{ marginTop: 4 }}>Community stats, question calibration, and the job-market pulse — all computed, never invented.</p>
      <div className="card" style={{ marginTop: 20, padding: 28, textAlign: 'center' }}>
        <span className="pill warn">beta — early data</span>
        <h3 style={{ marginTop: 12 }}>The community counters switch on soon</h3>
        <p className="small muted" style={{ marginTop: 8, maxWidth: 460, marginInline: 'auto' }}>
          This page will show checks taken this week, the most-attempted topics, live question
          recalibration events, and the monthly job-market pulse — once the beta has real traffic
          to report. No fake numbers in the meantime.
        </p>
        {local > 0 && <p className="small" style={{ marginTop: 12 }}>Your own contribution so far: <b className="num">{local}</b> checks on this device.</p>}
        <Link className="btn" style={{ marginTop: 18 }} to="/">Add a data point</Link>
      </div>
    </div>
  )
}

export function Methodology() {
  return (
    <div className="container fade-in" style={{ maxWidth: 680, padding: '32px 20px' }}>
      <h1 style={{ fontSize: '1.8rem' }}>How this works</h1>
      <p style={{ marginTop: 10 }}>
        <b>Questions.</b> Every question is original, written against a named public source, checked by an
        independent review pass for exactly one defensible answer, then human-reviewed before it counts.
        Spot a bad one? Every question will carry a report link.
      </p>
      <p style={{ marginTop: 10 }}>
        <b>Difficulty.</b> Each question starts with an estimated difficulty and recalibrates from real
        answers using an Elo update — the same math chess ratings use. Your six questions are chosen to
        match the level a quick first question suggests.
      </p>
      <p style={{ marginTop: 10 }}>
        <b>Percentiles.</b> "Top 27% of 412 this month" means exactly that: your result placed against every
        real session on that topic in the last 90 days. Until a topic has 30+ sessions, we say
        "early data" instead of faking authority.
      </p>
      <p style={{ marginTop: 10 }}>
        <b>Privacy.</b> No accounts. Your results live in your browser, exportable and erasable on the
        Progress page. The only thing recorded centrally is an anonymous answer log (question id,
        right/wrong, response time) that powers calibration — never who you are.
      </p>
      <h3 style={{ marginTop: 24 }}>For the technical reader</h3>
      <p className="small muted" style={{ marginTop: 6 }}>
        Item ratings: R = 1500 − 400·log₁₀(p/(1−p)), updated with K = 32/(1+n/40), floor 4, first
        exposures only. Session ability starts at 1350/1500/1650 by placement route, K = 48. Live
        calibration curves (estimated vs observed difficulty) and the retirement log will render here
        from real data as the beta grows. Full architecture in the{' '}
        <a href="https://github.com/lyhjeremy/skill-compass">repo</a>.
      </p>
      <QuotaMeter />
    </div>
  )
}

export function About() {
  return (
    <div className="container fade-in" style={{ maxWidth: 680, padding: '32px 20px' }}>
      <h1 style={{ fontSize: '1.8rem' }}>About</h1>
      <p style={{ marginTop: 10 }}>
        SkillCompass is built by <b>Jeremy Lee</b> — a data scientist (UCLA Anderson MSBA) who wanted an
        honest answer to "where do I actually stand?" that didn't require a sign-up, a subscription, or
        pretending a streak is a skill.
      </p>
      <p style={{ marginTop: 10 }}>
        The stack: React + TypeScript on GitHub Pages, a Python FastAPI + LangGraph service on Hugging
        Face Spaces, Elo-based calibration over an anonymous response log, and a daily-refreshed corpus
        of real job postings. Total infrastructure cost: $0/month.
      </p>
      <p style={{ marginTop: 14 }}>
        <a href="https://github.com/lyhjeremy">GitHub</a> · <a href="https://www.linkedin.com/in/lyhjeremy">LinkedIn</a>
      </p>
      <h3 style={{ marginTop: 24 }}>Privacy</h3>
      <p className="small muted" style={{ marginTop: 6 }}>
        No accounts, no tracking cookies. Everything about you stays in your browser's local storage —
        export or erase it on the Progress page. Future resume analysis runs in memory and stores
        nothing. Practice content referencing certificates (CFA, Google, AWS) is original and not
        affiliated with or endorsed by those organizations.
      </p>
    </div>
  )
}

export function NotFound() {
  return (
    <div className="container" style={{ padding: 60, textAlign: 'center' }}>
      <h2>Lost your bearing?</h2>
      <Link className="btn" style={{ marginTop: 16 }} to="/">Back to the compass</Link>
    </div>
  )
}
