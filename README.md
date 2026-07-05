# SkillCompass

**Know where you stand. See exactly where to go.**

A calibrated skill-assessment platform for data, analytics, and finance
professionals — free, no sign-up, wired to the live job market.

**▶️ Live (beta): https://lyhjeremy.github.io/skill-compass/**

Take a 2-minute skill check → get a score with a live percentile, a knowledge
map of what's strong and shaky, and a personalized study guide you keep.
Career tracks compare your evidence against what this month's real job
postings demand; a mock-interview agent stress-tests you at your own level.

## How it's built

| Layer | Stack | Runs on |
|---|---|---|
| Frontend | React + Vite + TypeScript | GitHub Pages (static) |
| API & agents | Python FastAPI + LangGraph | Hugging Face Spaces (free tier) |
| Calibration data | Anonymous response log | Supabase Postgres (free tier) |
| Content pipeline | `claude -p` generate → independent verify → human review | local / offline |
| Data refresh | Scheduled GitHub Actions | daily / weekly crons |

Total infrastructure cost: **$0/month**. No accounts, no cookies beyond
localStorage, resumes analyzed in memory and never stored.

## Repo layout

```
frontend/   React app (quiz engine, knowledge map, results — all client-side)
backend/    FastAPI service (aggregates, gap RAG, interview & guide agents)
content/    Question banks, concept graphs, resource DB (JSON, human-reviewed)
scripts/    Content-generation pipeline and cron jobs
docs/       Screenshots and design references
```

## Files

| File | Purpose |
|---|---|
| `frontend/src/lib/elo.ts` | Elo calibration formulas (item difficulty + session ability) |
| `frontend/src/lib/store.ts` | localStorage schema `sc_v1` — all user state lives on-device |
| `content/manifest.json` | Themes, tracks, subtopics — the app renders from this |
| `scripts/gen_questions.py` | Two-pass question generation (draft → adversarial verify) |
| `backend/app/main.py` | API surface (`/api/health`, `/api/aggregates`, …) |

## Running locally

```bash
cd frontend && npm install && npm run dev     # app on :5173
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

## Status

**Beta** — quiz engine, calibration, and the Data Analyst track are live.
Resume gap reports, mock interviews, study guides, and the remaining tracks
are in active development. Roadmap in `writeup.md`.

MIT © 2026 Jeremy Lee
