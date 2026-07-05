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
  const icon = theme === 'light' ? '☀️' : theme === 'dark' ? '🌙' : '🖥️'
  return (
    <button className="textlink" style={{ textDecoration: 'none', fontSize: '1rem' }}
      onClick={() => setTheme(next)} title={`Theme: ${theme} — click for ${next}`}
      aria-label={`Switch theme (current: ${theme})`}>{icon}</button>
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
