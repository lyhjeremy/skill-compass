"""SkillCompass API — Phase 2.

Anonymous response log + live percentiles, on a Supabase (Postgres) free tier.
Degrades gracefully to "early data" when Supabase isn't configured, so it is safe
to deploy before the secrets exist. No personal data is ever stored — only item
ids, correctness, timing, and a random per-session hash.
"""
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="SkillCompass API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lyhjeremy.github.io", "http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

STARTED = time.time()
COLD_START_MIN = 30           # sessions before a subtopic shows a real percentile
WINDOW_DAYS = 90             # rolling window for the distribution

# ---- Supabase client (lazy, optional) -------------------------------------
_sb = None
def sb():
    global _sb
    if _sb is None:
        url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
        if not (url and key):
            return None
        from supabase import create_client
        _sb = create_client(url, key)
    return _sb

# ---- tiny in-memory rate limiter ------------------------------------------
_hits: dict[str, deque] = defaultdict(deque)
def rate_ok(ip: str, limit: int, window_s: int) -> bool:
    now = time.time()
    q = _hits[ip]
    while q and q[0] < now - window_s:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True

def client_ip(req: Request) -> str:
    fwd = req.headers.get("x-forwarded-for")
    return (fwd.split(",")[0].strip() if fwd else (req.client.host if req.client else "unknown"))

def cutoff_iso() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).isoformat()


# ---- models ----------------------------------------------------------------
class ResponseIn(BaseModel):
    item_id: str
    concept: str | None = None
    correct: bool
    response_ms: int | None = None
    first_exposure: bool = True

class SessionIn(BaseModel):
    session_hash: str = Field(min_length=6, max_length=64)
    subtopic: str
    variant: str | None = None
    score: int
    total: int
    final_rating: float
    responses: list[ResponseIn] = []

class FeedbackIn(BaseModel):
    kind: str
    item_id: str | None = None
    body: str = Field(max_length=2000)


# ---- endpoints -------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "uptime_s": round(time.time() - STARTED),
        "supabase": sb() is not None,
        "llm": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GITHUB_MODELS_TOKEN")),
        "phase": "2-calibration",
    }


@app.post("/api/session")
def log_session(body: SessionIn, request: Request):
    """Log a completed quiz, return the live percentile for its subtopic."""
    if not rate_ok(client_ip(request), limit=40, window_s=3600):
        return {"ok": False, "reason": "rate-limited", "percentile": None, "cold_start": True}
    client = sb()
    if client is None:
        return {"ok": False, "reason": "no-db", "percentile": None, "cold_start": True}
    try:
        client.table("sessions").insert({
            "session_hash": body.session_hash, "subtopic": body.subtopic,
            "variant": body.variant, "score": body.score, "total": body.total,
            "final_rating": body.final_rating,
        }).execute()
        if body.responses:
            client.table("responses").insert([{
                "session_hash": body.session_hash, "item_id": r.item_id, "subtopic": body.subtopic,
                "concept": r.concept, "correct": r.correct, "response_ms": r.response_ms,
                "first_exposure": r.first_exposure,
            } for r in body.responses]).execute()

        cut = cutoff_iso()
        n = client.table("sessions").select("id", count="exact").eq("subtopic", body.subtopic)\
            .gte("created_at", cut).execute().count or 0
        if n < COLD_START_MIN:
            return {"ok": True, "n": n, "percentile": None, "cold_start": True}
        lower = client.table("sessions").select("id", count="exact").eq("subtopic", body.subtopic)\
            .gte("created_at", cut).lt("final_rating", body.final_rating).execute().count or 0
        better_than = round(lower / max(1, n - 1) * 100)
        return {"ok": True, "n": n, "better_than_pct": better_than,
                "top_pct": max(1, 100 - better_than), "percentile": better_than, "cold_start": False}
    except Exception as e:
        return {"ok": False, "reason": str(e)[:120], "percentile": None, "cold_start": True}


@app.get("/api/aggregates")
def aggregates(subtopic: str | None = None):
    client = sb()
    if client is None:
        return {"subtopic": subtopic, "n": 0, "status": "no-db"}
    try:
        cut = cutoff_iso()
        q = client.table("sessions").select("id", count="exact").gte("created_at", cut)
        if subtopic:
            q = q.eq("subtopic", subtopic)
        n = q.execute().count or 0
        return {"subtopic": subtopic, "n": n, "window_days": WINDOW_DAYS,
                "status": "live" if n >= COLD_START_MIN else "early-data"}
    except Exception as e:
        return {"subtopic": subtopic, "n": 0, "status": "error", "detail": str(e)[:120]}


@app.post("/api/feedback")
def feedback(body: FeedbackIn, request: Request):
    if not rate_ok(client_ip(request), limit=20, window_s=3600):
        return {"stored": False, "reason": "rate-limited"}
    client = sb()
    if client is None:
        return {"stored": False, "reason": "no-db"}
    try:
        client.table("feedback").insert({
            "kind": body.kind, "item_id": body.item_id, "body": body.body,
        }).execute()
        return {"stored": True}
    except Exception as e:
        return {"stored": False, "reason": str(e)[:120]}


@app.post("/api/resume")
@app.post("/api/gap")
@app.post("/api/interview")
@app.post("/api/guide")
def not_yet():
    return {"error": "coming-soon", "detail": "This endpoint lands in beta phases 3-5."}
