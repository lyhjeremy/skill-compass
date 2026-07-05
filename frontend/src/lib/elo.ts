import type { Item } from './types'

/** Elo calibration formulas — spec §7. Server-side recalibration lands in
 *  Phase 2; the same math ships here for set selection and future display. */

/** difficulty prior p (P(correct) for median visitor) -> item Elo rating */
export const itemRating = (p: number) => 1500 - 400 * Math.log10(p / (1 - p))

export const expectedScore = (rItem: number, rSess: number) =>
  1 / (1 + 10 ** ((rItem - rSess) / 400))

export const PLACEMENT_START = { easy: 1350, standard: 1500, hard: 1650 } as const

/** session ability update, K=48 (spec §7) */
export const updateSession = (rSess: number, rItem: number, correct: boolean) =>
  rSess + 48 * ((correct ? 1 : 0) - expectedScore(rItem, rSess))

/** The placement item: closest to median difficulty. */
export function placementItem(items: Item[]): Item {
  const sorted = [...items].sort((a, b) => a.difficulty_prior - b.difficulty_prior)
  return sorted[Math.floor(sorted.length / 2)]
}

/** Route from the placement answer: wrong -> easy; right & slow -> standard; right & fast -> hard. */
export function routePlacement(correct: boolean, ms: number): 'easy' | 'standard' | 'hard' {
  if (!correct) return 'easy'
  return ms < 20_000 ? 'hard' : 'standard'
}

/** Draw a 6-question set for a variant, unseen-first (spec §7 retakes). */
export function drawSet(items: Item[], variant: 'easy' | 'standard' | 'hard', seen: Set<string>, exclude?: string): Item[] {
  const pool = items.filter(i => i.id !== exclude)
  // high p = easier. easy: easiest first; hard: hardest first; standard: middle out.
  const byEase = [...pool].sort((a, b) => b.difficulty_prior - a.difficulty_prior)
  let ordered: Item[]
  if (variant === 'easy') ordered = byEase
  else if (variant === 'hard') ordered = [...byEase].reverse()
  else {
    const mid = byEase.length / 2
    ordered = [...byEase].sort((a, b) =>
      Math.abs(byEase.indexOf(a) - mid) - Math.abs(byEase.indexOf(b) - mid))
  }
  const unseen = ordered.filter(i => !seen.has(i.id))
  const rest = ordered.filter(i => seen.has(i.id))
  return [...unseen, ...rest].slice(0, 6)
}
