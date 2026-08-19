import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './styles.css'
import App from './App'
import { initTheme } from './components/ui'
import Home from './pages/Home'
import Explore from './pages/Explore'
import Quiz from './pages/Quiz'
import Results from './pages/Results'
import Progress from './pages/Progress'
import Track from './pages/Track'
import Interview from './pages/Interview'
import { About, Dashboard, Methodology, NotFound } from './pages/Static'

initTheme()

// GitHub Pages SPA: restore path stashed by 404.html
const stashed = sessionStorage.getItem('sc_redirect')
if (stashed) { sessionStorage.removeItem('sc_redirect'); history.replaceState(null, '', stashed) }

const router = createBrowserRouter([
  {
    path: '/', element: <App />, children: [
      { index: true, element: <Home /> },
      { path: 'explore', element: <Explore /> },
      { path: 'quiz/:subtopicId', element: <Quiz /> },
      { path: 'results/:sessionId', element: <Results /> },
      { path: 'progress', element: <Progress /> },
      { path: 'tracks/:trackId', element: <Track /> },
      { path: 'interview/:trackId', element: <Interview /> },
      { path: 'live', element: <Dashboard /> },
      { path: 'methodology', element: <Methodology /> },
      { path: 'about', element: <About /> },
      { path: '*', element: <NotFound /> },
    ],
  },
], { basename: '/skill-compass' })

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><RouterProvider router={router} /></React.StrictMode>,
)
