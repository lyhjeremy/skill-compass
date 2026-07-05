"""SkillCompass API — Phase 0 skeleton.

Runs on Hugging Face Spaces (Docker, free tier). The quiz loop never touches
this service; it powers aggregates, and later the gap-report RAG, interview
agent, and study-guide generator (Phases 2-5).
"""
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SkillCompass API", version="0.1.0")

ALLOWED_ORIGINS = [
    "https://lyhjeremy.github.io",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

STARTED = time.time()


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "uptime_s": round(time.time() - STARTED),
        "supabase": bool(os.environ.get("SUPABASE_URL")),
        "llm": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GITHUB_MODELS_TOKEN")),
        "phase": "0-scaffold",
    }


@app.get("/api/aggregates")
def aggregates(subtopic: str | None = None):
    # Phase 2: real rolling-90-day distributions from Supabase. Until then the
    # frontend shows honest "early data" labels; this shape is the contract.
    return {"subtopic": subtopic, "n": 0, "status": "early-data"}


@app.post("/api/event")
def event():
    # Phase 2: batched anonymous response log -> Supabase. No-op until wired.
    return {"stored": False, "reason": "phase-2"}


@app.post("/api/resume")
@app.post("/api/gap")
@app.post("/api/interview")
@app.post("/api/guide")
def not_yet():
    return {"error": "coming-soon", "detail": "This endpoint lands in beta phases 3-5."}
