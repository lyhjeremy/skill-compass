# Building SkillCompass

The goal: a live product that answers three questions for any data/analytics/finance
professional — *where do I stand, what does the market want, what should I do next* —
in under three minutes, with no sign-up, on $0/month infrastructure.

## Design decisions worth stealing

**The quiz loop makes zero server calls.** Questions ship as static JSON; scoring,
knowledge-map coloring, and the diagnosis are all client-side. The product's core
experience cannot go down and cannot degrade — LLM endpoints only power the
extras (gap reports, interviews, guides).

**Calibration is boring math, on purpose.** Item difficulty starts as an
LLM-estimated prior and recalibrates from real responses with a decaying-K Elo
update (`R = 1500 − 400·log₁₀(p/(1−p))`, K_item = 32/(1+n/40), K_session = 48).
Every rule is a few lines of explainable code — no black boxes between a user
and their percentile.

**Honesty as a feature.** Percentiles only appear at n ≥ 30 sessions ("early
data" labels before that); retakes draw unseen questions but the first attempt
locks the percentile; every question shows its public source. The methodology
page will render the live calibration curve — priors vs. observed — in public.

**Content pipeline mirrors the product's skepticism.** A generator drafts
questions in difficulty bands; a second, independent reviewer pass hunts for the
exact failure modes in the item rubric (ambiguous keys, giveaway option lengths,
trick phrasing) and repairs or rejects; a human reviews before anything counts.

**Privacy by architecture, not policy.** No accounts. All user state is
localStorage (`sc_v1`), exportable and erasable from the Progress page. The only
central record is an anonymous answer log. Future resume analysis reads the PDF
in-browser and sends only text, processed in memory.

## Status log

- **2026-07-05 — Phase 0-1 core.** Monorepo; design system (warm paper, Alegreya
  Sans/Source Sans 3, teal accent, validated theme palette); full quiz engine
  (placement routing, unseen-first draws, per-answer explanations, reveal beat);
  results with rule-based direct-coach diagnosis + interactive knowledge map;
  Progress page with export/erase; Data Analyst track hub; FastAPI skeleton +
  Dockerfile for HF Spaces; CI for Pages + Space deploys; question pipeline
  generating the first six subtopics. Verified end-to-end with a scripted
  click-through on a 390px viewport, light and dark.

- **2026-07-07 — 10× catalog scale-up.** Introduced `content/catalog.json` as the
  single source of truth: 160+ subtopics across 22 fields (software, web, cloud,
  security, marketing, product/UX, PM, HR, healthcare, sustainability, law, econ,
  accounting, math, psychology, + the original data/finance core) and 28 career
  tracks, referencing Coursera/edX/Kaplan curricula. `build_manifest.py` derives
  live/partial/soon status from whatever content exists, so subtopics, themes, and
  tracks flip live automatically as banks land — no manual edits. The generator is
  now catalog-driven, variable-sized (popular topics target 30 questions), and both
  resumable and rate-limit aware (extends short topics, stops cleanly on quota).
  Explore/Home/Track pages redesigned to stay scannable at this scale (ready-first
  sorting, collapsed upcoming fields, per-track readiness badges). Public beta
  shipped: **lyhjeremy.github.io/skill-compass**, GitHub Pages + Actions, SPA
  routing via a 404.html redirect shim.

- **2026-07-08 — Phase 2: live percentiles.** FastAPI backend on a Hugging Face
  Space (Docker, free CPU) logs every completed session to Supabase (Postgres,
  free tier) and returns a real percentile once a subtopic clears 30 sessions —
  before that, an honest "early data" label instead of a fabricated number.
  `supabase-py`'s SDK turned out to locally mis-parse Supabase's newer
  `sb_secret_...` key format as an invalid JWT before any request even went out;
  replaced it with a ~40-line stdlib-`urllib` PostgREST client, which sidesteps
  the bug and drops a dependency. Elo-style calibration throughout: item
  difficulty from a prior, session ability from a decaying-K update, percentile
  from a rolling 90-day window.

- **2026-07-08 — Phase 3: three AI features, real end to end.** Gemini (free
  tier) wired in with the same stdlib-REST pattern as Supabase, for three
  features that all reuse one `gemini_generate()` helper:
  - **Resume gap report** — paste resume text, get it matched against a track's
    own curriculum (never fabricated job-market stats — there's no postings
    corpus yet, so the guide doesn't pretend there is). Ephemeral: the text is
    used for one call and never stored.
  - **Mock interview capstone** — a real 6-8 turn text interview, seniority
    pitched to demonstrated mastery, that asks follow-ups on thin answers and
    ends with a per-dimension scorecard. Stateless by design: the frontend
    resends the transcript each turn, so there's no server-side session to leak.
    Verified it isn't a rubber stamp — a deliberately vague test answer got
    correctly flagged and scored low across several follow-ups.
  - **Study guide generator** — a personalized, downloadable Markdown plan for
    an entire track, built from real per-concept quiz results and, when
    present, resume and interview context too.

  Three real bugs surfaced and fixed by testing against production, not just
  local mocks:
  1. `gemini-2.0-flash` silently has no free-tier quota anymore (429 on a brand
     new key); switched the default to `gemini-2.5-flash`.
  2. `gemini-2.5-flash` spends its output-token budget on invisible "thinking"
     tokens by default, which was silently truncating responses (sometimes to
     zero visible text) before any JSON or Markdown had a chance to complete.
     Fixed with `thinkingConfig.thinkingBudget: 0` — none of these calls need
     chain-of-thought.
  3. The Hugging Face deploy pipeline was intermittently leaving the backend on
     a stale build despite the git push *and* a restart call both reporting
     success. Root cause: a plain `restart` can just restart the existing
     container without forcing a rebuild; the correct call is
     `restart?factory=true` (found by reading `huggingface_hub`'s own source,
     since the REST docs don't spell it out). The deploy workflow also switched
     from a fresh orphan `git init` + force-push every run to a normal
     incremental commit on the Space's real history — more reliable and closer
     to how the platform is actually meant to be used.

## Where it stands

Live at **lyhjeremy.github.io/skill-compass** — 4 fully-live career tracks (Data
Analyst, Data Scientist/ML, BI Analyst, Business/Product Analytics), 29 of 385
catalog subtopics live (~645 reviewed questions), all three Phase 3 AI features
working end-to-end against a $0/month stack (GitHub Pages, a Hugging Face Space,
Supabase free tier, Gemini free tier). Content generation for the remaining
catalog continues in the background.

## Next

Job-postings corpus + real market-demand gap analysis (the resume feature's
honest placeholder for now). Continued content generation across the 385-topic
catalog. Spec: `SKILLCOMPASS_SPEC.md` in the project folder.
