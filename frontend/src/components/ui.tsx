import { useEffect, useState } from 'react'

export function Logo({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 46 46" aria-hidden>
      <circle cx="23" cy="23" r="21" fill="none" stroke="var(--accent)" strokeWidth="3.5" />
      <path d="M23 8 L28 23 L23 38 L18 23 Z" fill="var(--accent)" />
      <circle cx="23" cy="23" r="3.4" fill="var(--paper)" />
    </svg>
  )
}

export function Wordmark() {
  return (<span style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }}>Skill<b style={{ color: 'var(--accent)' }}>Compass</b></span>)
}

function applyTheme(t: string) {
  const dark = t === 'dark' || (t === 'system' && matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}

export function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem('sc_theme') ?? 'system')
  useEffect(() => { applyTheme(theme); localStorage.setItem('sc_theme', theme) }, [theme])
  const next = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'
  const icons: Record<string, JSX.Element> = {
    light: <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="4.5" /><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8" /></svg>,
    dark: <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>,
    system: <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none" /></svg>,
  }
  return (
    <button className="textlink" style={{ textDecoration: 'none', color: 'var(--muted)' }}
      onClick={() => setTheme(next)} title={`Theme: ${theme} — click for ${next}`}
      aria-label={`Switch theme (current: ${theme})`}>{icons[theme]}</button>
  )
}

export function initTheme() { applyTheme(localStorage.getItem('sc_theme') ?? 'system') }

/** small stroke icons for the tab bar */
export const Icons = {
  home: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h5v-6h4v6h5V9.5" /></svg>,
  explore: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>,
  progress: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 3a9 9 0 1 1-9 9" /><path d="M12 7v5l4 2.5" strokeWidth="1.6" /></svg>,
  live: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>,
}
