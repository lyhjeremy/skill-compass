#!/usr/bin/env python3
"""SkillCompass content pipeline: draft -> adversarial verify -> difficulty prior.

Uses the local `claude -p` CLI (Claude Max, $0 marginal). Two independent passes
per batch mirror the pattern proven in cantonese-learner-v2: a generator drafts
questions, then a separate reviewer persona hunts for exactly the failure modes
in the item rubric (ambiguous keys, giveaway option lengths, trick phrasing)
and repairs or rejects. Human review remains the final gate before launch.

Usage:
  python3 scripts/gen_questions.py --subtopic sql-querying
  python3 scripts/gen_questions.py --all
"""
import argparse, json, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
WORKING = CONTENT / "_working"
OUT = CONTENT / "subtopics"
MODEL = "sonnet"
PER_BATCH = 5
BATCHES = 4  # 20 items per subtopic

SUBTOPIC_BRIEFS = {
    "sql-querying": "SQL for analysts: SELECT/WHERE/GROUP BY, joins (inner/left/anti), aggregation, window functions, CTEs, NULL semantics, query correctness pitfalls. Ground in PostgreSQL documentation concepts.",
    "spreadsheets": "Excel/Google Sheets for analysts: lookups (VLOOKUP/XLOOKUP/INDEX-MATCH), absolute vs relative references, pivot tables, common formula errors, data cleaning, when spreadsheets break down.",
    "descriptive-stats": "Descriptive statistics: mean vs median under skew, standard deviation, percentiles, distributions, correlation vs causation, sampling basics, misleading summary statistics.",
    "dashboards-bi": "Dashboards & BI: choosing chart types, KPI design, dashboard layout principles, misleading visualizations, aggregation granularity, BI tool concepts (filters, drill-down, refresh).",
    "ab-testing": "A/B testing for analysts: hypothesis setup, significance and p-values, power and sample size, common pitfalls (peeking, multiple comparisons, novelty effects), interpreting results honestly.",
    "data-storytelling": "Data storytelling: structuring an insight narrative, leading with the answer, audience-appropriate framing, honest uncertainty communication, chart annotation, executive summaries.",
    # --- Data Scientist / ML track (Coursera ML & IBM DS inspired) ---
    "ml-fundamentals": "Machine learning fundamentals: supervised vs unsupervised learning, classification vs regression tasks, train/validation/test splits, overfitting and underfitting, bias-variance tradeoff, why cross-validation. Coursera Machine Learning-level intuition, scenario-based, no heavy math.",
    "feature-engineering-data-prep": "Preparing data for models: handling missing values, one-hot vs label encoding, feature scaling and when it matters, target leakage, outlier treatment, class imbalance handling. Practical scenarios an ML practitioner faces.",
    "regression-basics": "Regression for analysts: interpreting linear regression coefficients and intercepts, R-squared meaning and limits, residual patterns, multicollinearity symptoms, when logistic regression applies, odds ratios, extrapolation dangers.",
    "model-evaluation": "Evaluating ML models: accuracy limits under class imbalance, precision vs recall tradeoffs, F1, confusion matrices, ROC-AUC vs precision-recall curves, classification threshold selection, probability calibration, validation vs test sets.",
    "python-for-data": "Python for data analysis with pandas: DataFrame vs Series, filtering with boolean masks, groupby aggregations, merge/join types and row-explosion pitfalls, handling NaN, vectorization vs loops, common gotchas (SettingWithCopyWarning, chained indexing).",
    "statistical-inference": "Statistical inference: interpreting confidence intervals correctly, standard error vs standard deviation, Central Limit Theorem in practice, t-tests, Type I vs Type II errors, sample vs population, statistical vs practical significance.",
    # --- Stats & Quant (edX MITx / Kaplan CFA quant methods inspired) ---
    "probability-basics": "Applied probability: conditional probability, independence, Bayes' theorem with base rates (diagnostic-test and fraud-detection scenarios), expected value decisions, binomial vs normal vs Poisson and when each applies. CFA quantitative-methods level, simple numbers.",
    # --- Finance & Markets (Kaplan / CFA Level I inspired; conceptual, calculator-free) ---
    "time-value-of-money": "Time value of money: present vs future value intuition, compounding frequency effects, annuities vs perpetuities, NPV decision rule, IRR and its pitfalls, choosing discount rates. CFA Level I quant-methods style with simple round numbers.",
    "financial-statements": "Reading financial statements: what lives on the income statement vs balance sheet vs cash flow statement, gross/operating/net margins, accrual vs cash accounting, working capital, current ratio, ROE, debt-to-equity, linking the three statements. CFA Level I FRA-inspired.",
    "portfolio-risk-return": "Portfolio risk and return: why diversification works and its limits, correlation's role, systematic vs idiosyncratic risk, beta interpretation, Sharpe ratio comparisons, risk-return tradeoff, rebalancing logic. CFA Level I portfolio-management-inspired, conceptual.",
    # --- Business Analytics (Coursera business analytics inspired) ---
    "business-metrics-kpis": "Business and product metrics: CAC and LTV and their ratio, churn vs retention math, conversion funnel analysis, MRR/ARR, cohort views, choosing a north-star metric, spotting vanity metrics. Realistic startup/enterprise scenarios.",
    "forecasting-basics": "Business forecasting: separating trend, seasonality, and noise; moving averages and exponential smoothing intuition; forecast error measures (MAE, MAPE, bias); naive baselines as benchmarks; forecast horizons and uncertainty growth; when judgment should override the model.",
}

RUBRIC = """Every question MUST pass ALL of these:
1. Exactly one defensible correct answer; a domain expert would not argue.
2. Three plausible distractors drawn from real misconceptions - not throwaways.
3. Options parallel in form and length (the correct answer must NOT be the longest).
4. No "all/none of the above". At most 1 in 10 uses "which is NOT".
5. Stem <= 45 words, self-contained, scenario-based where possible, no trick phrasing or trivia.
6. Explanation <= 60 words; names why the key distractor is wrong when non-obvious.
7. grounding.source is a real, well-known public reference (official docs, Wikipedia article title, widely-known textbook); grounding.note is one line on what it supports. Do not invent URLs.
8. Plain professional English; no culture-specific idioms."""


def claude(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            r = subprocess.run(
                ["claude", "-p", prompt, "--model", MODEL],
                capture_output=True, text=True, timeout=420,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
            print(f"  retry {attempt+1}: rc={r.returncode} {r.stderr[:120]}", flush=True)
        except subprocess.TimeoutExpired:
            print(f"  retry {attempt+1}: timeout", flush=True)
        time.sleep(10 * (attempt + 1))
    raise RuntimeError("claude -p failed after retries")


def parse_json(text: str):
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start = min([i for i in (text.find("["), text.find("{")) if i >= 0])
    return json.loads(text[start:])


def gen_concepts(sid: str, brief: str):
    prompt = f"""You are designing the concept map for a skill-assessment subtopic.
Subtopic: {SUBTOPIC_BRIEFS and brief}
Return ONLY a JSON array of exactly 8 concepts, ordered roughly from prerequisite to advanced:
[{{"id":"kebab-case-id","label":"2-4 word label","definition":"one plain-English sentence","prereq":"id of the single most direct prerequisite concept in this list, or null"}}]"""
    concepts = parse_json(claude(prompt))
    # deterministic two-row layout for the knowledge map (viewBox 340x150)
    for i, c in enumerate(concepts):
        row, col = divmod(i, 4)
        c["x"] = 50 + col * 80
        c["y"] = 38 + row * 74
    return concepts


def gen_batch(sid: str, brief: str, concepts, batch_idx: int, seen_stems):
    concept_ids = [c["id"] for c in concepts]
    difficulty_slice = ["mostly easy (p~0.7-0.85)", "easy-to-medium (p~0.55-0.7)",
                        "medium-to-hard (p~0.4-0.55)", "hard (p~0.25-0.4)"][batch_idx]
    avoid = "\n".join(f"- {s}" for s in seen_stems[-25:]) or "(none yet)"
    prompt = f"""Write {PER_BATCH} original multiple-choice questions for a professional skill assessment.
Subtopic: {brief}
Difficulty band for THIS batch: {difficulty_slice} (p = probability a median professional answers correctly).
Tag each question with exactly one concept id from: {concept_ids}
Cover different concepts across the batch. Do NOT duplicate or closely resemble these existing stems:
{avoid}

{RUBRIC}

Return ONLY a JSON array:
[{{"concept":"<id>","stem":"...","options":["...","...","...","..."],"answer":0,
"explanation":"...","grounding":{{"source":"...","note":"..."}},"difficulty_prior":0.6}}]"""
    return parse_json(claude(prompt))


def verify_batch(brief: str, items):
    prompt = f"""You are an independent, skeptical exam reviewer. You did NOT write these questions.
Subtopic: {brief}
For EACH question below: check it against every rubric rule; fix any violation by rewriting
the minimal part (stem, options, answer index, explanation); re-estimate difficulty_prior
(p = probability a median professional answers correctly, 0.15-0.9); set "verdict" to
"keep" or "reject" (reject only if unfixable: no defensible single answer).
Rules:
{RUBRIC}

Questions:
{json.dumps(items, ensure_ascii=False)}

Return ONLY the corrected JSON array, same schema plus "verdict"."""
    return parse_json(claude(prompt))


def build_subtopic(sid: str):
    brief = SUBTOPIC_BRIEFS[sid]
    WORKING.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"[{sid}] concepts...", flush=True)
    concepts = gen_concepts(sid, brief)
    items, seen = [], []
    for b in range(BATCHES):
        print(f"[{sid}] batch {b+1}/{BATCHES} draft...", flush=True)
        draft = gen_batch(sid, brief, concepts, b, seen)
        (WORKING / f"{sid}-b{b}-draft.json").write_text(json.dumps(draft, indent=1))
        print(f"[{sid}] batch {b+1}/{BATCHES} verify...", flush=True)
        checked = verify_batch(brief, draft)
        (WORKING / f"{sid}-b{b}-verified.json").write_text(json.dumps(checked, indent=1))
        for q in checked:
            if q.get("verdict") == "keep" and q.get("concept") and len(q.get("options", [])) == 4:
                q.pop("verdict", None)
                q["id"] = f"{sid}-{len(items):03d}"
                q["status"] = "beta"  # pending human review
                items.append(q)
                seen.append(q["stem"][:80])
    out = {"id": sid, "concepts": concepts, "items": items,
           "generated": "claude sonnet draft+verify, pending human review"}
    (OUT / f"{sid}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"[{sid}] DONE: {len(items)} items kept", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subtopic")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true", help="regenerate even if output exists")
    args = ap.parse_args()
    targets = list(SUBTOPIC_BRIEFS) if args.all else [args.subtopic]
    for sid in targets:
        if not args.force and (OUT / f"{sid}.json").exists():
            print(f"[{sid}] exists, skipping (use --force to regenerate)", flush=True)
            continue
        try:
            build_subtopic(sid)
        except Exception as e:
            print(f"[{sid}] FAILED: {e}", flush=True)
