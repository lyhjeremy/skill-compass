# Building SkillCompass

The goal: a live product that answers three questions for a data, analytics or finance professional (where do I stand, what does the market want, what should I do next) in under three minutes, with no sign-up, on $0/month infrastructure.

## Design decisions

**The quiz loop makes no server calls.** Questions ship as static JSON, and scoring, knowledge-map coloring and the diagnosis all run in the browser. The core experience keeps working when the backend is down. The LLM endpoints only power the extras: gap reports, interviews and study guides.

**Calibration is plain math, on purpose.** Each item starts with an LLM-estimated difficulty prior *p*, converted to an Elo rating with `R = 1500 − 400·log₁₀(p/(1−p))`. The session's ability rating updates after every answer with K = 48. The percentile ranks the session's final rating against other sessions on the same subtopic. Every rule is a few lines of code that can be explained to the person being scored. The planned item recalibration from real responses (a decaying K of 32/(1+n/40)) is documented on the app's How it works page and the response log it needs is being collected, but the update itself is not implemented yet; item ratings still come from the priors.

**Honesty as a feature.** Percentiles appear only once a subtopic has 30 sessions; before that the app says "early data". Retakes draw unseen questions, and every question shows its public source.

**The content pipeline is skeptical.** A generator drafts questions in difficulty bands. A second, independent reviewer pass looks for the failure modes in the item rubric (ambiguous keys, giveaway option lengths, trick phrasing) and repairs or rejects. A human reviews before anything goes live.

**Privacy by architecture.** There are no accounts. All user state is in localStorage (`sc_v1`) and can be exported or erased from the Progress page. The only central record is an anonymous answer log. Resume text is used for one call and not stored.

## Status log

- **2026-07-05, Phase 0 and 1 core.** Monorepo; design system; the full quiz engine (placement routing, unseen-first draws, per-answer explanations, a reveal step); results with a rule-based diagnosis and an interactive knowledge map; a Progress page with export and erase; the Data Analyst track hub; a FastAPI skeleton and Dockerfile for Hugging Face Spaces; CI for the Pages and Space deploys; and the question pipeline generating the first six subtopics. Verified end to end with a scripted click-through at 390px, in light and dark themes.

- **2026-07-07, 10× catalog scale-up.** `content/catalog.json` became the single source of truth: 160+ subtopics across 22 fields and 28 career tracks at the time, referencing Coursera, edX and Kaplan curricula. `build_manifest.py` derives live, partial or coming-soon status from whatever content exists, so subtopics, fields and tracks go live automatically as banks land. The generator became catalog-driven, variable-sized (popular topics target 30 questions), resumable and rate-limit aware. The Explore, Home and Track pages were redesigned to stay scannable at this scale. Public beta shipped at **lyhjeremy.github.io/skill-compass** on GitHub Pages, with SPA routing through a 404.html redirect.

- **2026-07-08, Phase 2: live percentiles.** A FastAPI backend on a Hugging Face Space (Docker, free CPU) logs every completed session to Supabase (Postgres, free tier) and returns a real percentile once a subtopic clears 30 sessions, from a rolling 90-day window. `supabase-py` mis-parsed Supabase's newer `sb_secret_...` key format as an invalid JWT before any request went out, so I replaced it with a stdlib `urllib` PostgREST client of about 40 lines, which avoided the bug and dropped a dependency.

- **2026-07-08, Phase 3: three LLM features, end to end.** Gemini (free tier) is wired in with the same stdlib REST pattern, and all three features share one `gemini_generate()` helper:
  - **Resume gap report.** Paste a resume and it is matched against a track's own curriculum. There is no job-postings corpus yet, so the report does not invent market statistics. The text is used for one call and not stored.
  - **Mock interview capstone.** A 6 to 8 turn text interview, pitched to the level the user has demonstrated, that asks follow-ups on thin answers and ends with a per-dimension scorecard. It is stateless: the frontend resends the transcript each turn, so there is no server-side session to leak. I checked that it does not rubber-stamp: a deliberately vague test answer was flagged and scored low across several follow-ups.
  - **Study guide generator.** A downloadable Markdown plan for a whole track, built from per-concept quiz results and, when present, the resume and interview context.

  Testing against production found three bugs:
  1. `gemini-2.0-flash` had no free-tier quota anymore (429 on a new key), so the default moved to `gemini-2.5-flash`.
  2. `gemini-2.5-flash` spends its output-token budget on hidden "thinking" tokens by default, which truncated responses, sometimes to no visible text, before the JSON or Markdown could finish. Setting `thinkingConfig.thinkingBudget: 0` fixed it; none of these calls needs chain-of-thought.
  3. The Hugging Face deploy sometimes left the backend on a stale build even though the git push and the restart call both reported success. A plain `restart` can restart the existing container without rebuilding; the right call is `restart?factory=true`, which I found by reading `huggingface_hub`'s source because the REST docs do not cover it. The workflow also moved from a fresh orphan `git init` and force-push on every run to a normal incremental commit on the Space's history, which proved more reliable.

- **2026-07-29, a silent outage, and the monitoring that hid it.** The calibration store had been unreachable for an unknown stretch and nothing reported it. Three faults stacked up.

  The Supabase project had been **paused for inactivity**. A paused free project loses its DNS record, so the host answered NXDOMAIN and the Space logged `connection failed: [Errno -2] Name or service not known`. No session was being written, so no subtopic could reach the 30-session threshold. The headline feature was frozen while the UI fell back to its "early data" label and looked normal.

  The pause came from the keep-alive cron meant to prevent it: it ran **weekly** against a **7-day** inactivity threshold. With the guard interval equal to the threshold, one delayed run trips the pause, and GitHub drops scheduled runs on shared runners routinely. The cron now runs `17 3 * * 1,4` (Monday and Thursday): a 4-day nominal gap, 3 days of slack and two chances a week to fire. A guard interval has to be shorter than the threshold it guards.

  The outage was hidden by `curl --fail` on `/api/aggregates`. That endpoint answers **200** with `{"status":"error", "detail": ...}` when the Supabase read fails, and `--fail` only reads the status line, so three weekly runs passed through a total outage. `/api/health` has the same problem: its top-level `"ok"` stays `true` while its `"supabase"` field is `false`. The cron now checks both response bodies and writes to `$GITHUB_STEP_SUMMARY`. I ran it against production in both states: red at 18:25 with Supabase down, green at 22:30 with it up.

  Resuming the project from the dashboard restored everything. The pre-pause data was intact, and `/api/aggregates` came back `{"n":51,"window_days":90,"status":"live"}`. Recovery went NXDOMAIN, then DNS within 30 seconds, then Cloudflare **521** while the origin came up, then PostgREST **PGRST205** ("could not find the table 'public.sessions' in the schema cache") for two or three minutes while the cache reloaded, then healthy. The PGRST205 stage looks like a missing migration and is not one.

- **2026-07-29, product overview page.** A standalone page at `/overview/` (source `frontend/public/overview/index.html`) that leads on the gap between what a resume claims and what a check can prove, with eleven screenshots of the running app. It uses the app's own verdict vocabulary (strong, shaky, missed, and the dashed ring of an untested claim) as its structure, and its palette and type come from `frontend/src/styles.css`, so a theme change in the app should be carried over to it. Its counts were taken from `content/catalog.json` and the question banks.

## Where it stands

Live at **lyhjeremy.github.io/skill-compass** with 4 career tracks fully live (Data Analyst, Data Scientist/ML, BI Analyst, Business/Product Analytics), 29 of the 385 catalog subtopics across 46 fields and 117 tracks, and 645 reviewed questions. All three LLM features work end to end on a $0/month stack: GitHub Pages, a Hugging Face Space, Supabase free tier and Gemini free tier. Content generation for the rest of the catalog continues in the background. After the July 29 recovery the store held 51 sessions in the rolling 90-day window.

## Next

A job-postings corpus and a real market-demand gap analysis, which the resume feature currently leaves out. Item recalibration from the logged responses. Content for the rest of the 385-subtopic catalog. The spec is `SKILLCOMPASS_SPEC.md` in the project folder.
