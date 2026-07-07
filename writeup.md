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
  sorting, collapsed upcoming fields, per-track readiness badges).

## Next

Phase 2: anonymous event log → Supabase, live Elo recalibration, real
percentiles, public dashboard. Phase 3: job-postings corpus + resume gap
reports. Phase 4-5: study-guide generator, mock-interview agent. Spec:
`SKILLCOMPASS_SPEC.md` in the project folder.
