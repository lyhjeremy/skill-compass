---
title: SkillCompass API
emoji: 🧭
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# SkillCompass API

FastAPI service deployed to a Hugging Face Space (Docker SDK, free CPU tier).
The YAML block above is the Space config Hugging Face reads — keep it at the top.

## Deploy (one-time setup)

1. Create a free account at huggingface.co, then **New Space** → name
   `skillcompass-api` → SDK **Docker** → hardware **CPU basic (free)**.
2. Add secrets in Space settings: `SUPABASE_URL`, `SUPABASE_KEY` (live
   percentiles), `GEMINI_API_KEY` (resume analysis, mock interview, study
   guide — all three AI features run on this one key). Optionally
   `GEMINI_MODEL` to override the default (`gemini-2.5-flash`; `2.0-flash`
   has no free-tier quota as of mid-2026).
3. Push this `backend/` directory to the Space. CI does this automatically
   on every push to `backend/**` (`.github/workflows/deploy-space.yml`) —
   note that a plain HF "restart" can leave the Space on a stale build; the
   workflow calls `restart?factory=true` to force an actual rebuild.

Local dev: `pip install -r requirements.txt && uvicorn app.main:app --reload`
Health check: `GET /api/health` — reports real Supabase/Gemini connectivity
(cached 120s), not just whether the secrets are present.

Not implemented (deferred, no account set up yet): a job-postings corpus for
real market-demand data would need `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` or similar
— genuinely a new account Jeremy would need to create, unlike everything above.
