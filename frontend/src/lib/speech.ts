// Web Speech API integration for the voice mock-interview upgrade
// (GAP_UPGRADES_SPEC.md upgrade 1). Client-side, $0, no API key.
//
// The Web Speech API's SpeechRecognition interface isn't part of TypeScript's
// standard DOM lib (it's non-standard / Chromium+Safari only, absent in
// Firefox), so we declare the minimal shape we use ourselves rather than
// pulling in a third-party @types package for a handful of fields.

interface SpeechRecognitionResultLike {
  isFinal: boolean
  0: { transcript: string }
}

interface SpeechRecognitionEventLike extends Event {
  resultIndex: number
  results: ArrayLike<SpeechRecognitionResultLike>
}

interface SpeechRecognitionLike extends EventTarget {
  lang: string
  continuous: boolean
  interimResults: boolean
  start(): void
  stop(): void
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: ((event: Event) => void) | null
  onend: (() => void) | null
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

export function isSpeechRecognitionSupported(): boolean {
  return getSpeechRecognitionCtor() !== null
}

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

export type SpeechRecognitionHandle = {
  stop: () => void
}

/** Starts listening; calls onInterim with the running transcript as it's
 * recognized (so the caller can show live feedback), and onFinal once with
 * the complete recognized text when the user stops speaking. The caller is
 * expected to let the user review/edit the text before submitting it --
 * speech-recognition errors shouldn't silently tank an interview answer. */
export function startListening(opts: {
  onInterim: (text: string) => void
  onFinal: (text: string) => void
  onError: (message: string) => void
}): SpeechRecognitionHandle | null {
  const Ctor = getSpeechRecognitionCtor()
  if (!Ctor) {
    opts.onError('Voice input is not supported in this browser -- try Chrome, Edge, or Safari.')
    return null
  }

  const recognition = new Ctor()
  recognition.lang = 'en-US'
  recognition.continuous = false
  recognition.interimResults = true

  let finalTranscript = ''
  recognition.onresult = (event) => {
    let interim = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i]
      if (result.isFinal) finalTranscript += result[0].transcript
      else interim += result[0].transcript
    }
    opts.onInterim(finalTranscript + interim)
  }
  recognition.onerror = () => {
    opts.onError("Didn't catch that -- try again, or just type your answer.")
  }
  recognition.onend = () => {
    if (finalTranscript.trim()) opts.onFinal(finalTranscript.trim())
  }

  recognition.start()
  return { stop: () => recognition.stop() }
}

/** Reads text aloud using the browser's built-in TTS voices. Fire-and-forget;
 * callers that want a mute toggle should simply not call this. */
export function speak(text: string): void {
  if (!isSpeechSynthesisSupported()) return
  window.speechSynthesis.cancel() // don't stack overlapping utterances
  const utterance = new SpeechSynthesisUtterance(text)
  window.speechSynthesis.speak(utterance)
}

export function stopSpeaking(): void {
  if (isSpeechSynthesisSupported()) window.speechSynthesis.cancel()
}
