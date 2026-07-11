import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { interviewTurn, llmErrorMessage, warmBackend } from '../lib/api'
import { getManifest } from '../lib/content'
import {
  isSpeechRecognitionSupported, isSpeechSynthesisSupported,
  speak, startListening, stopSpeaking,
  type SpeechRecognitionHandle,
} from '../lib/speech'
import { store } from '../lib/store'
import type { InterviewScorecard, InterviewSeniority, InterviewTurn, Manifest } from '../lib/types'

type Phase = 'loading' | 'locked' | 'intro' | 'chatting' | 'done'
const SENIORITY_LABEL: Record<InterviewSeniority, string> = { entry: 'entry-level', mid: 'mid-level', senior: 'senior-level' }
const MAX_TURNS = 7

export default function Interview() {
  const { trackId = '' } = useParams()
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [phase, setPhase] = useState<Phase>('loading')
  const [transcript, setTranscript] = useState<InterviewTurn[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scorecard, setScorecard] = useState<InterviewScorecard | null>(null)
  const [seniority, setSeniority] = useState<InterviewSeniority>('mid')
  const [listening, setListening] = useState(false)
  const [voiceMuted, setVoiceMuted] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognitionHandle | null>(null)
  const voiceInputSupported = isSpeechRecognitionSupported()
  const voiceOutputSupported = isSpeechSynthesisSupported()

  useEffect(() => { warmBackend(); getManifest().then(setManifest).catch(console.error) }, [])

  useEffect(() => () => stopSpeaking(), []) // stop any speech if the user navigates away

  useEffect(() => {
    if (!manifest) return
    const track = manifest.tracks.find(t => t.id === trackId)
    if (!track || track.status !== 'live') { setPhase('locked'); return }
    const subs = track.subtopics.map(id => manifest.subtopics.find(s => s.id === id)!).filter(Boolean)
    const masteries = subs.map(s => store.mastery(s.id))
    const known = masteries.filter((m): m is number => m !== null)
    if (known.length === 0 || known.length !== masteries.length) { setPhase('locked'); return }
    const overall = Math.round(known.reduce((sum, m) => sum + m, 0) / known.length)
    setSeniority(overall >= 75 ? 'senior' : overall >= 50 ? 'mid' : 'entry')

    const prior = store.interview(trackId)
    if (prior && !store.canStartInterview(trackId)) {
      setScorecard(prior.scorecard); setTranscript(prior.transcript); setPhase('done')
      return
    }
    setPhase('intro')
  }, [manifest, trackId])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [transcript, busy])

  if (!manifest || phase === 'loading') return <div className="container" style={{ padding: 48 }}><p className="muted">Loading…</p></div>

  if (phase === 'locked') return (
    <div className="container fade-in" style={{ padding: 48, textAlign: 'center' }}>
      <h2>Not unlocked yet</h2>
      <p className="muted small" style={{ marginTop: 8 }}>Complete every topic in this track first — the interview matches its questions to what you've actually shown you know.</p>
      <Link className="btn" style={{ marginTop: 16 }} to={`/tracks/${trackId}`}>Back to the track</Link>
    </div>
  )

  const track = manifest.tracks.find(t => t.id === trackId)!
  const topics = track.subtopics.map(id => manifest.subtopics.find(s => s.id === id)?.title).filter((x): x is string => !!x)

  async function sendTurn(next: InterviewTurn[]) {
    setBusy(true); setError(null)
    const r = await interviewTurn(track.title, seniority, topics, next.map(t => ({ role: t.role, text: t.text })))
    setBusy(false)
    if (!r.ok || !r.message) { setError(llmErrorMessage(r.reason)); return }
    const updated: InterviewTurn[] = [...next, { role: 'interviewer', text: r.message }]
    setTranscript(updated)
    if (!voiceMuted) speak(r.message)
    if (r.done && r.scorecard) {
      setScorecard(r.scorecard)
      store.setInterview({ trackId, seniority, transcript: updated, scorecard: r.scorecard, completedAt: Date.now() })
      setPhase('done')
    }
  }

  function start() { setPhase('chatting'); sendTurn([]) }

  function send() {
    const text = input.trim()
    if (!text || busy) return
    setInput('')
    sendTurn([...transcript, { role: 'candidate', text }])
  }

  function toggleMic() {
    if (listening) {
      recognitionRef.current?.stop()
      recognitionRef.current = null
      setListening(false)
      return
    }
    setError(null)
    const handle = startListening({
      onInterim: setInput,
      onFinal: setInput, // final transcript lands in the textarea for review/edit before Send -- a speech-recognition slip shouldn't silently tank an answer
      onError: (message) => { setError(message); setListening(false) },
    })
    if (handle) { recognitionRef.current = handle; setListening(true) }
  }

  if (phase === 'intro') return (
    <div className="container fade-in" style={{ maxWidth: 560, padding: '48px 20px' }}>
      <div className="card raised" style={{ textAlign: 'center', padding: 28 }}>
        <span className="pill">{track.title} · {SENIORITY_LABEL[seniority]}</span>
        <h2 style={{ marginTop: 12 }}>Your mock interview</h2>
        <p className="muted" style={{ marginTop: 8 }}>~10 minutes · 6–8 questions · honest feedback</p>
        <p className="small muted" style={{ marginTop: 6 }}>
          Pitched at {SENIORITY_LABEL[seniority]}, based on what you've shown across this track. Real
          questions, follow-ups when an answer is thin, and a scorecard at the end — professional, not harsh.
        </p>
        <button className="btn" style={{ marginTop: 18 }} onClick={start}>Start the interview</button>
        <p style={{ marginTop: 10 }}><Link className="textlink small" to={`/tracks/${trackId}`}>Not now</Link></p>
      </div>
    </div>
  )

  if (phase === 'done' && scorecard) return (
    <div className="container fade-in" style={{ maxWidth: 640, padding: '32px 20px' }}>
      <span className="pill">{track.title} · {SENIORITY_LABEL[seniority]}</span>
      <h2 style={{ marginTop: 10 }}>Your scorecard</h2>
      <div className="card raised" style={{ marginTop: 14 }}>
        <div className="scorecard-row">
          {(['accuracy', 'depth', 'clarity'] as const).map(k => (
            <div key={k} className="metric">
              <div className="lbl"><span style={{ textTransform: 'capitalize' }}>{k}</span><span className="num">{scorecard[k]}/5</span></div>
              <div className="track thin"><div className={`fill ${scorecard[k] >= 4 ? 'good' : scorecard[k] >= 3 ? 'warn' : 'bad'}`} style={{ width: `${scorecard[k] / 5 * 100}%` }} /></div>
            </div>
          ))}
        </div>
        <div className="explain" style={{ marginTop: 16 }}><b>Strengthen:</b> {scorecard.strengthen}</div>
      </div>
      <details style={{ marginTop: 18 }}>
        <summary className="small muted" style={{ cursor: 'pointer' }}>Read the full transcript</summary>
        <div className="chat" style={{ marginTop: 12 }}>
          {transcript.map((t, i) => (
            <div key={i} className={`bub ${t.role === 'interviewer' ? 'ai' : 'me'}`}>
              <div className="who">{t.role === 'interviewer' ? 'Interviewer' : 'You'}</div>{t.text}
            </div>
          ))}
        </div>
      </details>
      <div style={{ marginTop: 20 }}><Link className="btn ghost" to={`/tracks/${trackId}`}>Back to the track</Link></div>
      <p className="small muted" style={{ marginTop: 14 }}>One interview per track per day — come back tomorrow for another.</p>
    </div>
  )

  const askedCount = Math.min(transcript.filter(t => t.role === 'interviewer').length + (busy ? 1 : 0), MAX_TURNS)
  return (
    <div className="container fade-in" style={{ maxWidth: 640, padding: '24px 20px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span className="pill gray">{track.title} · {SENIORITY_LABEL[seniority]}</span>
        <span className="small muted">question {Math.max(askedCount, 1)} of ~{MAX_TURNS}</span>
      </div>
      <div className="chat">
        {transcript.map((t, i) => (
          <div key={i} className={`bub ${t.role === 'interviewer' ? 'ai' : 'me'}`}>
            <div className="who">{t.role === 'interviewer' ? 'Interviewer' : 'You'}</div>{t.text}
          </div>
        ))}
        {busy && <div className="bub ai"><div className="who">Interviewer</div><div className="typing-dots"><i /><i /><i /></div></div>}
        <div ref={bottomRef} />
      </div>
      {error && <p className="small" style={{ color: 'var(--bad)', marginTop: 10 }}>{error}</p>}
      <div className="chat-input-row">
        <textarea
          value={input} onChange={e => setInput(e.target.value)} disabled={busy}
          placeholder={listening ? 'Listening…' : 'Type your answer…'} rows={1}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
        />
        {voiceInputSupported && (
          <button
            className={`mic-btn${listening ? ' active' : ''}`} onClick={toggleMic} disabled={busy}
            title={listening ? 'Stop listening' : 'Speak your answer'}
            aria-label={listening ? 'Stop listening' : 'Speak your answer'}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <rect x="9" y="2" width="6" height="12" rx="3" /><path d="M5 10v1a7 7 0 0 0 14 0v-1M12 18v4" />
            </svg>
          </button>
        )}
        <button className="btn" style={{ padding: '11px 20px' }} onClick={send} disabled={busy || !input.trim()}>Send</button>
      </div>
      <p className="small muted" style={{ marginTop: 8 }}>
        Press Enter to send, Shift+Enter for a new line.
        {voiceInputSupported && ' Or tap the mic and speak — review the text before sending.'}
        {voiceOutputSupported && (
          <> · <button className="textlink small" style={{ padding: 0 }} onClick={() => { setVoiceMuted(m => !m); if (!voiceMuted) stopSpeaking() }}>
            {voiceMuted ? 'Unmute interviewer voice' : 'Mute interviewer voice'}
          </button></>
        )}
      </p>
    </div>
  )
}
