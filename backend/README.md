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
2. Add secrets in Space settings when each phase needs them:
   `SUPABASE_URL`, `SUPABASE_KEY` (Phase 2), `GEMINI_API_KEY`,
   `GITHUB_MODELS_TOKEN`, `ADZUNA_APP_ID/KEY`, `TURNSTILE_SECRET` (Phase 3).
3. Push this `backend/` directory to the Space (CI does this automatically
   once `HF_TOKEN` is set as a GitHub Actions secret — see
   `.github/workflows/deploy-space.yml`).

Local dev: `pip install -r requirements.txt && uvicorn app.main:app --reload`
Health check: `GET /api/health`
