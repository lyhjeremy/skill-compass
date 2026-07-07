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

export interface AnswerRecord { itemId: string; concept: string; correct: boolean; ms: number }
export interface Session {
  id: string; subtopic: string; ts: number; variant: 'easy' | 'standard' | 'hard';
  correct: number; total: number; answers: AnswerRecord[]; avgMs: number;
}
export type ConceptState = 'strong' | 'shaky' | 'missed' | 'untested'
