import { Link, NavLink, Outlet, ScrollRestoration } from 'react-router-dom'
import { Icons, Logo, ThemeToggle, Wordmark } from './components/ui'

const tabs = [
  { to: '/', label: 'Home', icon: Icons.home },
  { to: '/explore', label: 'Explore', icon: Icons.explore },
  { to: '/progress', label: 'Progress', icon: Icons.progress },
  { to: '/live', label: 'Live', icon: Icons.live },
]

export default function App() {
  return (
    <>
      <nav className="topnav">
        <Link to="/" className="wordmark"><Logo /> <Wordmark /></Link>
        <div className="links">
          <NavLink to="/explore">Explore</NavLink>
          <NavLink to="/tracks/data-analyst">Tracks</NavLink>
          <NavLink to="/progress">Progress</NavLink>
          <NavLink to="/live">Dashboard</NavLink>
          <NavLink to="/methodology">How it works</NavLink>
          <ThemeToggle />
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
      <footer className="site container">
        <span>Built by <a href="https://github.com/lyhjeremy">Jeremy Lee</a> · <Link to="/about">About</Link></span>
        <span>
          <Link to="/methodology">How this works</Link> · <Link to="/about">Privacy</Link> ·{' '}
          <a href="https://github.com/lyhjeremy/skill-compass">GitHub</a>
        </span>
      </footer>
      <nav className="tabbar" aria-label="Primary">
        {tabs.map(t => (
          <NavLink key={t.to} to={t.to} className={({ isActive }) => isActive ? 'active' : ''} end={t.to === '/'}>
            {t.icon}<span>{t.label}</span>
          </NavLink>
        ))}
      </nav>
      <ScrollRestoration />
    </>
  )
}
