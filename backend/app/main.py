"""SkillCompass API — Phase 2.

Anonymous response log + live percentiles, on a Supabase (Postgres) free tier.
Talks to Supabase's PostgREST layer directly over HTTP (stdlib only) rather than
the `supabase-py` SDK, which as of mid-2026 locally mis-parses Supabase's newer
short-form `sb_secret_...` API keys as invalid JWTs before any request is even
sent. Plain REST calls work with both the legacy JWT service_role key and the
new secret-key format, and drop a dependency in the process.

Degrades gracefully to "early data" when Supabase isn't configured, so it is
safe to deploy before the secrets exist. No personal data is ever stored —
only item ids, correctness, timing, and a random per-session hash.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="SkillCompass API", version="0.2.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lyhjeremy.github.io", "http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

STARTED = time.time()
COLD_START_MIN = 30          # sessions before a subtopic shows a real percentile
WINDOW_DAYS = 90             # rolling window for the distribution


# ---- Supabase (direct PostgREST calls, no SDK) -----------------------------
SB_URL = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
SB_KEY = (os.environ.get("SUPABASE_KEY") or "").strip()

def env_shape(name: str) -> dict:
    """Safe, non-secret diagnostics: presence/length/prefix only, never the value."""
    v = os.environ.get(name)
    if not v:
        return {"present": False}
    return {"present": True, "len": len(v), "has_whitespace": v != v.strip(),
            "prefix": v[:8] if name.endswith("URL") else v[:3]}

def sb_ready() -> bool:
    return bool(SB_URL and SB_KEY)

def sb_request(method: str, path: str, body=None, extra_headers: dict | None = None):
    """One PostgREST call. Raises RuntimeError with a short, safe message on failure."""
    headers = {"apikey": SB_KEY, "Content-Type": "application/json"}
    # Legacy JWT keys (start with 'eyJ') are also accepted as a Bearer token; the
    # newer sb_secret_/sb_publishable_ keys are sent via the apikey header only.
    if SB_KEY.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {SB_KEY}"
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{SB_URL}/rest/v1/{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:200]
        raise RuntimeError(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"connection failed: {e.reason}"[:200])

def sb_insert(table: str, rows: list[dict]):
    sb_request("POST", table, body=rows, extra_headers={"Prefer": "return=minimal"})

def sb_count(table: str, filters: dict[str, str]) -> int:
    """Exact row count via PostgREST's Content-Range header; fetches 0 rows."""
    qs = urllib.parse.urlencode(filters)
    _, headers, _ = sb_request("GET", f"{table}?select=id&{qs}",
                                extra_headers={"Prefer": "count=exact", "Range": "0-0"})
    cr = headers.get("Content-Range") or headers.get("content-range") or ""
    total = cr.split("/")[-1] if "/" in cr else ""
    return int(total) if total.isdigit() else 0


# ---- Gemini (direct REST, no SDK — same reasoning as Supabase above) -------
GEMINI_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def gemini_ready() -> bool:
    return bool(GEMINI_KEY)

def gemini_generate(prompt: str, max_tokens: int = 512, json_mode: bool = False) -> str:
    """One Gemini call. Raises RuntimeError with a short, safe message on failure."""
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}")
    gen_config = {"maxOutputTokens": max_tokens}
    if json_mode:
        gen_config["responseMimeType"] = "application/json"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": gen_config}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:200]
        raise RuntimeError(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"connection failed: {e.reason}"[:200])
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"unexpected response shape: {str(data)[:200]}")


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
    out = {
        "ok": True,
        "uptime_s": round(time.time() - STARTED),
        "supabase": False,
        "supabase_error": None,
        "supabase_url": env_shape("SUPABASE_URL"),
        "supabase_key": env_shape("SUPABASE_KEY"),
        "llm": False,
        "llm_error": None,
        "llm_key": env_shape("GEMINI_API_KEY"),
        "llm_model": GEMINI_MODEL,
        "phase": "3-ai-features",
    }
    if sb_ready():
        try:
            sb_count("sessions", {"created_at": f"gte.{cutoff_iso()}"})
            out["supabase"] = True
        except Exception as e:
            out["supabase_error"] = str(e)
    if gemini_ready():
        try:
            reply = gemini_generate("Reply with exactly: OK", max_tokens=5)
            out["llm"] = "OK" in reply
            if not out["llm"]:
                out["llm_error"] = f"unexpected reply: {reply[:80]!r}"
        except Exception as e:
            out["llm_error"] = str(e)
    return out


@app.post("/api/session")
def log_session(body: SessionIn, request: Request):
    """Log a completed quiz, return the live percentile for its subtopic."""
    if not rate_ok(client_ip(request), limit=40, window_s=3600):
        return {"ok": False, "reason": "rate-limited", "percentile": None, "cold_start": True}
    if not sb_ready():
        return {"ok": False, "reason": "no-db", "percentile": None, "cold_start": True}
    try:
        sb_insert("sessions", [{
            "session_hash": body.session_hash, "subtopic": body.subtopic,
            "variant": body.variant, "score": body.score, "total": body.total,
            "final_rating": body.final_rating,
        }])
        if body.responses:
            sb_insert("responses", [{
                "session_hash": body.session_hash, "item_id": r.item_id, "subtopic": body.subtopic,
                "concept": r.concept, "correct": r.correct, "response_ms": r.response_ms,
                "first_exposure": r.first_exposure,
            } for r in body.responses])

        cut = cutoff_iso()
        n = sb_count("sessions", {"subtopic": f"eq.{body.subtopic}", "created_at": f"gte.{cut}"})
        if n < COLD_START_MIN:
            return {"ok": True, "n": n, "percentile": None, "cold_start": True}
        lower = sb_count("sessions", {"subtopic": f"eq.{body.subtopic}", "created_at": f"gte.{cut}",
                                       "final_rating": f"lt.{body.final_rating}"})
        better_than = round(lower / max(1, n - 1) * 100)
        return {"ok": True, "n": n, "better_than_pct": better_than,
                "top_pct": max(1, 100 - better_than), "percentile": better_than, "cold_start": False}
    except Exception as e:
        return {"ok": False, "reason": str(e)[:160], "percentile": None, "cold_start": True}


@app.get("/api/aggregates")
def aggregates(subtopic: str | None = None):
    if not sb_ready():
        return {"subtopic": subtopic, "n": 0, "status": "no-db"}
    try:
        filters = {"created_at": f"gte.{cutoff_iso()}"}
        if subtopic:
            filters["subtopic"] = f"eq.{subtopic}"
        n = sb_count("sessions", filters)
        return {"subtopic": subtopic, "n": n, "window_days": WINDOW_DAYS,
                "status": "live" if n >= COLD_START_MIN else "early-data"}
    except Exception as e:
        return {"subtopic": subtopic, "n": 0, "status": "error", "detail": str(e)[:160]}


@app.post("/api/feedback")
def feedback(body: FeedbackIn, request: Request):
    if not rate_ok(client_ip(request), limit=20, window_s=3600):
        return {"stored": False, "reason": "rate-limited"}
    if not sb_ready():
        return {"stored": False, "reason": "no-db"}
    try:
        sb_insert("feedback", [{"kind": body.kind, "item_id": body.item_id, "body": body.body}])
        return {"stored": True}
    except Exception as e:
        return {"stored": False, "reason": str(e)[:160]}


@app.post("/api/resume")
@app.post("/api/gap")
@app.post("/api/interview")
@app.post("/api/guide")
def not_yet():
    return {"error": "coming-soon", "detail": "This endpoint lands in beta phases 3-5."}
