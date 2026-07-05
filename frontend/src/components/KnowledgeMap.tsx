import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Concept, ConceptState, SubtopicContent } from '../lib/types'

const COLORS: Record<ConceptState, string> = {
  strong: 'var(--good)', shaky: 'var(--warn)', missed: 'var(--bad)', untested: 'transparent',
}

/** The knowledge map: precomputed layout, status-colored nodes, tap -> concept
 *  sheet (spec §5.5). Untested nodes render hollow. */
export function KnowledgeMap({ content, states, missedStems, retakeTo }: {
  content: SubtopicContent
  states: Record<string, ConceptState>
  missedStems: Record<string, string>
  retakeTo: string
}) {
  const [open, setOpen] = useState<Concept | null>(null)
  const byId = new Map(content.concepts.map(c => [c.id, c]))
  return (
    <div style={{ position: 'relative' }}>
      <svg viewBox="0 0 340 150" style={{ width: '100%', maxWidth: 560 }} role="img"
        aria-label="Knowledge map of concepts, colored by your results">
        {content.concepts.map(c => {
          const p = c.prereq ? byId.get(c.prereq) : null
          return p ? <line key={`e${c.id}`} x1={p.x} y1={p.y} x2={c.x} y2={c.y}
            stroke="var(--border)" strokeWidth="2" /> : null
        })}
        {content.concepts.map(c => {
          const st = states[c.id] ?? 'untested'
          return (
            <g key={c.id} onClick={() => setOpen(c)} style={{ cursor: 'pointer' }}>
              <circle cx={c.x} cy={c.y} r="16" fill="transparent" />
              <circle cx={c.x} cy={c.y} r="11" fill={st === 'untested' ? 'var(--card)' : COLORS[st]}
                stroke={st === 'untested' ? 'var(--faint)' : COLORS[st]}
                strokeWidth="2" strokeDasharray={st === 'untested' ? '3 2' : undefined} />
              <text x={c.x} y={c.y + 24} fontSize="7.5" textAnchor="middle" fill="var(--muted)">{c.label}</text>
            </g>
          )
        })}
      </svg>
      <div className="legend" style={{ marginTop: 6 }}>
        <span><i style={{ background: 'var(--good)' }} />Strong</span>
        <span><i style={{ background: 'var(--warn)' }} />Shaky</span>
        <span><i style={{ background: 'var(--bad)' }} />Missed</span>
        <span><i style={{ background: 'var(--card)', border: '1.5px dashed var(--faint)' }} />Not yet tested</span>
      </div>
      {open && (
        <>
          <div className="overlay" onClick={() => setOpen(null)} />
          <div className="sheet fade-in" role="dialog" aria-label={`Concept: ${open.label}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <h3>{open.label}</h3>
              <span className={`pill ${states[open.id] === 'strong' ? 'green' : states[open.id] === 'untested' ? 'gray' : 'warn'}`}>{states[open.id]}</span>
            </div>
            <p className="small" style={{ marginTop: 8 }}>{open.definition}</p>
            {states[open.id] === 'untested' ? (
              <p className="small muted" style={{ marginTop: 10 }}>Take this check again to test this concept.</p>
            ) : missedStems[open.id] ? (
              <p className="small" style={{ marginTop: 10 }}><b>The question you missed:</b> <span className="muted">{missedStems[open.id]}</span></p>
            ) : null}
            <div style={{ marginTop: 14, display: 'flex', gap: 10 }}>
              <Link className="btn ghost" style={{ padding: '8px 18px' }} to={retakeTo}>Take it again</Link>
              <button className="textlink" onClick={() => setOpen(null)}>Close</button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
