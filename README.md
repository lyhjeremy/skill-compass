# SkillCompass

**Know where you stand. See exactly where to go.**

A calibrated skill-assessment platform spanning data, software, cloud, security,
business, finance, marketing, product, and more — free, no sign-up. The content
catalog (`content/catalog.json`) defines 385 subtopics across 46 fields and 117
career tracks; each goes live automatically as its reviewed question bank lands.

**▶️ Live (beta): https://lyhjeremy.github.io/skill-compass/**

Take a 2-minute skill check → get a score with a live percentile and a knowledge
map of what's strong and shaky. On a career track, once you've been assessed:
paste your resume to see which of the track's topics it already proves, take a
real AI mock interview pitched to your demonstrated level, and generate a
personalized study guide built from your actual results.

## How it's built

| Layer | Stack | Runs on |
|---|---|---|
| Frontend | React + Vite + TypeScript | GitHub Pages (static) |
| API | Python FastAPI, stdlib-only REST clients (no SDKs) | Hugging Face Spaces (free tier) |
| Calibration data | Anonymous response log | Supabase Postgres (free tier) |
| AI features | Gemini (resume analysis, mock interview, study guide) | Google AI free tier |
| Content pipeline | `claude -p` generate → independent verify → human review | local / offline |

Total infrastructure cost: **$0/month**. No accounts, no cookies beyond
localStorage, resumes analyzed in memory and never stored.

The AI features (`/api/resume`, `/api/interview`, `/api/guide`) are single-call
Gemini requests with the turn-taking and validation logic written in plain
Python — not LangGraph, which the original spec envisioned. Simpler, and one
fewer dependency to debug; see `writeup.md` for why.

## Repo layout

```
frontend/   React app (quiz engine, knowledge map, results — all client-side)
backend/    FastAPI service (percentiles, resume analysis, interview, study guide)
content/    Question banks, concept graphs (JSON, human-reviewed)
scripts/    Content-generation pipeline
docs/       Screenshots and design references
```

## Files

| File | Purpose |
|---|---|
| `frontend/src/lib/elo.ts` | Elo calibration formulas (item difficulty + session ability) |
| `frontend/src/lib/store.ts` | localStorage schema `sc_v1` — all user state lives on-device |
| `frontend/src/lib/api.ts` | Backend client for session logging + the three AI features |
| `content/manifest.json` | Themes, tracks, subtopics — the app renders from this |
| `scripts/gen_questions.py` | Two-pass question generation (draft → adversarial verify) |
| `backend/app/main.py` | API surface (`/api/health`, `/api/session`, `/api/resume`, `/api/interview`, `/api/guide`, …) |

## Running locally

```bash
cd frontend && npm install && npm run dev     # app on :5173
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

## Status

**Beta, feature-complete for Phase 3.** Live: the full quiz engine, 4 fully-live
career tracks (29 of 385 catalog subtopics, ~645 reviewed questions), live
percentiles, and all three AI features — resume gap report, mock interview
capstone, and the study guide generator. Content generation for the remaining
catalog continues in the background. A real job-postings corpus for market-demand
comparison (the resume feature's honest placeholder today) is the main deferred
item — full history in `writeup.md`.

MIT © 2026 Jeremy Lee
