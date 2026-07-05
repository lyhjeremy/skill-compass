import type { Concept, ConceptState, Session, SubtopicContent } from './types'

/** Direct-coach diagnosis (spec Appendix A): honest, specific, no padding,
 *  always ends on the next move. Rule-based — the quiz loop makes no LLM calls. */
export function composeDiagnosis(
  session: Session, content: SubtopicContent, states: Record<string, ConceptState>,
): { text: string; nextConcept: Concept | null } {
  const label = (id: string) => content.concepts.find(c => c.id === id)?.label ?? id
  const strong = content.concepts.filter(c => states[c.id] === 'strong' &&
    session.answers.some(a => a.concept === c.id))
  const weak = content.concepts.filter(c => states[c.id] === 'missed' || states[c.id] === 'shaky')
  const untested = content.concepts.filter(c => states[c.id] === 'untested')

  // hardest concept answered correctly = lowest-prior item they got right
  const hardestRight = session.answers
    .filter(a => a.correct)
    .map(a => content.items.find(i => i.id === a.itemId)!)
    .sort((a, b) => a.difficulty_prior - b.difficulty_prior)[0]

  const parts: string[] = []
  if (session.correct === session.total) {
    parts.push(`A clean ${session.correct}/${session.total}.`)
    if (hardestRight) parts.push(`You handled ${label(hardestRight.concept)} — the hardest idea in this set — without slipping.`)
    parts.push(untested.length
      ? `Take it again to cover ${label(untested[0].id).toLowerCase()}; a perfect run on fresh questions is the real test.`
      : 'Try the next subtopic up — this one looks solved.')
  } else {
    if (session.correct === 0) parts.push(`A tough draw — it happens, and it tells us exactly where to start.`)
    if (hardestRight) parts.push(`You reason well about ${label(hardestRight.concept).toLowerCase()}.`)
    else if (strong.length) parts.push(`${label(strong[0].id)} is solid.`)
    if (weak.length) {
      const w = weak[0]
      parts.push(`${label(w.id)} is your gap — ${states[w.id] === 'missed' ? 'the miss there was decisive' : 'your answers there were mixed'}. Start there.`)
    } else if (untested.length) {
      parts.push(`Nothing you answered was weak; ${untested.length} concepts are still untested — take it again to cover them.`)
    }
  }
  const nextConcept = weak[0] ?? untested[0] ?? null
  return { text: parts.join(' '), nextConcept }
}
