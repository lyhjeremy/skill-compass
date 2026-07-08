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

app = FastAPI(title="SkillCompass API", version="0.3.1")  # bump on every deploy — health exposes this
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

def gemini_generate(prompt: str, max_tokens: int = 512, json_mode: bool = False, _retried: bool = False) -> str:
    """One Gemini call, with one short retry on transient overload (HTTP 503 is
    common on the free tier under load — worth one retry before failing the request).
    Raises RuntimeError with a short, safe message on final failure."""
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
        detail = e.read().decode(errors="replace")[:800]
        if e.code == 503 and not _retried:
            time.sleep(2)
            return gemini_generate(prompt, max_tokens, json_mode, _retried=True)
        raise RuntimeError(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"connection failed: {e.reason}"[:200])
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"unexpected response shape: {str(data)[:200]}")

def gemini_error_reason(e: Exception) -> str:
    """Classify a gemini_generate() failure into a short, honest reason code —
    'the model is overloaded' is a very different user message from 'we're broken'."""
    msg = str(e)
    if "HTTP 503" in msg or "high demand" in msg.lower() or "overloaded" in msg.lower():
        return "llm-overloaded"
    if "HTTP 429" in msg or "quota" in msg.lower():
        return "llm-quota"
    if "HTTP 400" in msg or "HTTP 401" in msg or "HTTP 403" in msg:
        return "llm-misconfigured"
    return "llm-error"


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

class SubtopicRef(BaseModel):
    id: str
    title: str

class ResumeIn(BaseModel):
    text: str = Field(min_length=20, max_length=20000)
    subtopics: list[SubtopicRef] = Field(min_length=1, max_length=40)

class TranscriptTurn(BaseModel):
    role: str  # "interviewer" | "candidate"
    text: str = Field(max_length=4000)

class InterviewIn(BaseModel):
    track_title: str = Field(max_length=100)
    seniority: str = "mid"
    topics: list[str] = Field(min_length=1, max_length=12)
    transcript: list[TranscriptTurn] = Field(default_factory=list, max_length=40)


# ---- endpoints -------------------------------------------------------------
_health_cache: dict = {"ts": 0.0, "supabase": None, "supabase_error": None, "llm": None, "llm_error": None}
HEALTH_CHECK_TTL_S = 120  # a live connectivity check costs a real DB query / Gemini call —
                          # don't let frequent polling (deploy verification, uptime monitors) burn quota

@app.get("/api/health")
def health():
    out = {
        "ok": True,
        "version": app.version,
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
    stale = time.time() - _health_cache["ts"] > HEALTH_CHECK_TTL_S
    if stale:
        if sb_ready():
            try:
                sb_count("sessions", {"created_at": f"gte.{cutoff_iso()}"})
                _health_cache["supabase"], _health_cache["supabase_error"] = True, None
            except Exception as e:
                _health_cache["supabase"], _health_cache["supabase_error"] = False, str(e)
        if gemini_ready():
            try:
                reply = gemini_generate("Reply with exactly: OK", max_tokens=5)
                ok = "OK" in reply
                _health_cache["llm"] = ok
                _health_cache["llm_error"] = None if ok else f"unexpected reply: {reply[:80]!r}"
            except Exception as e:
                _health_cache["llm"], _health_cache["llm_error"] = False, str(e)
        _health_cache["ts"] = time.time()
    out["supabase"] = bool(_health_cache["supabase"])
    out["supabase_error"] = _health_cache["supabase_error"]
    out["llm"] = bool(_health_cache["llm"])
    out["llm_error"] = _health_cache["llm_error"]
    out["checked_s_ago"] = round(time.time() - _health_cache["ts"])
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
def analyze_resume(body: ResumeIn, request: Request):
    """Extract skills from resume text and match them against a track's subtopics.

    Ephemeral by design (spec §5.7): the text arrives in the request, is used for
    exactly one Gemini call, and nothing is written to Supabase or logged. Compares
    against the track's own curriculum only — no job-market claim is made here,
    since there is no postings corpus yet to back one honestly.
    """
    if not rate_ok(client_ip(request), limit=10, window_s=3600):
        return {"ok": False, "reason": "rate-limited"}
    if not gemini_ready():
        return {"ok": False, "reason": "llm-unavailable"}

    subtopic_list = "\n".join(f"- {s.id}: {s.title}" for s in body.subtopics)
    prompt = f"""You are assessing resume evidence against a specific list of skill areas.

Resume text:
\"\"\"
{body.text[:8000]}
\"\"\"

Skill areas (id: title):
{subtopic_list}

Return ONLY JSON with this exact shape, nothing else:
{{
  "skills": ["short skill phrase", ...up to 12, only skills clearly evidenced by the resume],
  "years_experience": <number, your best estimate of total professional experience, or null>,
  "evidenced_subtopic_ids": ["<id from the list above>", ...],
  "summary": "<one plain, specific sentence about their background, no fluff or flattery>"
}}
Be conservative on evidenced_subtopic_ids: include an id only if the resume gives concrete
evidence (a named tool, a project, a described responsibility) — not just an adjacent buzzword."""
    try:
        raw = gemini_generate(prompt, max_tokens=800, json_mode=True)
        data = json.loads(raw)
    except Exception as e:
        return {"ok": False, "reason": gemini_error_reason(e), "detail": str(e)[:160]}

    # Never trust the model's output shape blindly.
    valid_ids = {s.id for s in body.subtopics}
    evidenced = [i for i in data.get("evidenced_subtopic_ids", []) if isinstance(i, str) and i in valid_ids]
    skills = [str(s)[:60] for s in data.get("skills", []) if isinstance(s, str)][:12]
    years = data.get("years_experience")
    years = years if isinstance(years, (int, float)) and 0 <= years <= 60 else None
    summary = str(data.get("summary", ""))[:280]
    return {"ok": True, "skills": skills, "years_experience": years,
            "evidenced_subtopic_ids": evidenced, "summary": summary}


MAX_INTERVIEW_TURNS = 7  # ~10 minutes at 1-1.5 min/turn, matches the on-screen promise

@app.post("/api/interview")
def interview_turn(body: InterviewIn, request: Request):
    """One turn of a stateless mock interview. The frontend holds the transcript
    and resends it in full each turn — no server-side session to manage or leak.
    Turn counting (and therefore when the interview ends) is decided by this code,
    never trusted to the model; only the *content* of each turn is generated."""
    if not rate_ok(client_ip(request), limit=30, window_s=3600):
        return {"ok": False, "reason": "rate-limited"}
    if not gemini_ready():
        return {"ok": False, "reason": "llm-unavailable"}

    asked = sum(1 for t in body.transcript if t.role == "interviewer")
    turn_n = asked + 1
    is_final = turn_n >= MAX_INTERVIEW_TURNS
    seniority = body.seniority if body.seniority in ("entry", "mid", "senior") else "mid"
    topics = ", ".join(body.topics[:12])
    convo = "\n".join(
        f"{'Interviewer' if t.role == 'interviewer' else 'Candidate'}: {t.text}" for t in body.transcript
    ) or "(interview has not started yet)"

    if is_final:
        turn_instructions = ("This is the FINAL turn. Do not ask a new question. Instead: give "
                              "1-2 sentences of warm, honest closing remarks, then score the whole interview.")
    else:
        turn_instructions = ("Ask exactly ONE question: either a natural follow-up that probes their "
                              "last answer more deeply, or — if their last answer was already thorough — "
                              "a fresh question on a different topic from the list. 2-3 sentences max.")
        if turn_n == 1:
            turn_instructions += " This is the opening question — start warm and natural, like a real interview."

    prompt = f"""You are conducting a realistic job interview for a {seniority}-level {body.track_title} role.
Persona: professional and constructive. Ask real interview questions. When a candidate's answer is
weak, frame any eventual feedback as how to strengthen the answer — never harsh, never demoralizing,
always specific.

Topics this role covers: {topics}

This is interview turn {turn_n} of {MAX_INTERVIEW_TURNS}. {turn_instructions}

Conversation so far:
{convo}

Return ONLY JSON with this exact shape:
{{
  "message": "<your next question, follow-up, or closing remarks>",
  "is_followup": <true if this responds to the last answer, false if a fresh topic>,
  "scorecard": {"null (not the final turn)" if not is_final else '{"accuracy": <1-5 int>, "depth": <1-5 int>, "clarity": <1-5 int>, "strengthen": "<one concrete, specific sentence — the single highest-leverage thing to improve>"} — REQUIRED on this final turn'}
}}"""

    try:
        raw = gemini_generate(prompt, max_tokens=500, json_mode=True)
        data = json.loads(raw)
    except Exception as e:
        return {"ok": False, "reason": gemini_error_reason(e), "detail": str(e)[:160]}

    message = str(data.get("message", "")).strip()[:1000]
    if not message:
        message = ("Thanks for walking me through your thinking today." if is_final
                    else "Let's continue — tell me more about your approach.")

    scorecard = None
    if is_final:
        sc = data.get("scorecard") or {}
        def clamp15(v):
            try:
                n = int(v)
                return n if 1 <= n <= 5 else 3
            except (TypeError, ValueError):
                return 3
        scorecard = {
            "accuracy": clamp15(sc.get("accuracy")),
            "depth": clamp15(sc.get("depth")),
            "clarity": clamp15(sc.get("clarity")),
            "strengthen": (str(sc.get("strengthen", "")).strip()[:280]
                           or "Keep practicing articulating the reasoning behind your answers, not just the conclusions."),
        }

    return {"ok": True, "message": message, "done": is_final, "scorecard": scorecard}


@app.post("/api/gap")
@app.post("/api/guide")
def not_yet():
    return {"error": "coming-soon", "detail": "This endpoint lands later in the beta."}
