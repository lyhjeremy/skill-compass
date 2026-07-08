export interface Theme { id: string; title: string; color: string; status: 'live' | 'soon'; featured?: boolean }
export interface TrackDef { id: string; title: string; status: 'live' | 'partial' | 'soon'; blurb: string; subtopics: string[]; ready?: number; total?: number }
export interface CertDef { id: string; title: string; status: string; blurb: string }
export interface SubtopicMeta { id: string; title: string; theme: string; track: string; status: string }
export interface Manifest { version: number; themes: Theme[]; tracks: TrackDef[]; certs: CertDef[]; subtopics: SubtopicMeta[] }

export interface Concept { id: string; label: string; definition: string; prereq: string | null; x: number; y: number }
export interface Item {
  id: string; concept: string; stem: string; options: string[]; answer: number;
  explanation: string; grounding: { source: string; note: string }; difficulty_prior: number; status: string;
}
export interface SubtopicContent { id: string; concepts: Concept[]; items: Item[] }

export interface AnswerRecord { itemId: string; concept: string; correct: boolean; ms: number; p?: number }
export interface Session {
  id: string; subtopic: string; ts: number; variant: 'easy' | 'standard' | 'hard';
  correct: number; total: number; answers: AnswerRecord[]; avgMs: number;
  finalRating?: number;
  // filled in after the backend logs the session (Phase 2)
  posted?: boolean; percentile?: number | null; topPct?: number; nPeers?: number;
}
export type ConceptState = 'strong' | 'shaky' | 'missed' | 'untested'

export interface ResumeProfile {
  trackId: string
  skills: string[]
  yearsExperience: number | null
  evidencedSubtopicIds: string[]
  summary: string
  ts: number
}

export type InterviewSeniority = 'entry' | 'mid' | 'senior'
export interface InterviewTurn { role: 'interviewer' | 'candidate'; text: string }
export interface InterviewScorecard { accuracy: number; depth: number; clarity: number; strengthen: string }
export interface InterviewRecord {
  trackId: string; seniority: InterviewSeniority
  transcript: InterviewTurn[]; scorecard: InterviewScorecard; completedAt: number
}
