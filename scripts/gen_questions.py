#!/usr/bin/env python3
"""SkillCompass content pipeline: draft -> adversarial verify -> difficulty prior.

Catalog-driven. Reads content/catalog.json for each subtopic's brief and target
`size`, then for each subtopic: generates a concept map, drafts questions in
difficulty-graded batches, and runs an independent skeptical reviewer pass that
repairs or rejects against the item rubric. Human review is the final gate.

Resumable and quota-friendly: a subtopic already at (or above) its target size is
skipped; one that exists but is short is EXTENDED with additional batches. Safe to
kill and rerun — it picks up where it left off. Runs sequentially so it degrades
gracefully when the Claude Max CLI rate-limits.

Usage:
  python3 scripts/gen_questions.py --all              # every catalog subtopic, resume
  python3 scripts/gen_questions.py --subtopic sql-querying
  python3 scripts/gen_questions.py --all --limit 20   # stop after 20 subtopics this run
"""
import argparse, json, re, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
WORKING = CONTENT / "_working"
OUT = CONTENT / "subtopics"
MODEL = "sonnet"
PER_BATCH = 5

CATALOG = json.loads((CONTENT / "catalog.json").read_text())
BRIEF = {s["id"]: s["brief"] for s in CATALOG["subtopics"]}
SIZE = {s["id"]: s.get("size", 20) for s in CATALOG["subtopics"]}

RUBRIC = """Every question MUST pass ALL of these:
1. Exactly one defensible correct answer; a domain expert would not argue.
2. Three plausible distractors drawn from real misconceptions - not throwaways.
3. Options parallel in form and length (the correct answer must NOT be the longest).
4. No "all/none of the above". At most 1 in 10 uses "which is NOT".
5. Stem <= 45 words, self-contained, scenario-based where possible, no trick phrasing or trivia.
6. Explanation <= 60 words; names why the key distractor is wrong when non-obvious.
7. grounding.source is a real, well-known public reference (official docs, Wikipedia article title, widely-known textbook); grounding.note is one line on what it supports. Do not invent URLs.
8. Plain professional English; no culture-specific idioms. Content must be timeless — no "as of" dates, current office-holders, or latest-version numbers."""


def claude(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            r = subprocess.run(["claude", "-p", prompt, "--model", MODEL],
                               capture_output=True, text=True, timeout=420)
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


def layout(concepts):
    """Deterministic two-row layout for the knowledge map (viewBox 340x150)."""
    for i, c in enumerate(concepts):
        c["x"] = 50 + (i % 4) * 80
        c["y"] = 38 + (i // 4) * 74
    return concepts


def gen_concepts(brief: str):
    prompt = f"""You are designing the concept map for a skill-assessment subtopic.
Subtopic: {brief}
Return ONLY a JSON array of exactly 8 concepts, ordered roughly from prerequisite to advanced:
[{{"id":"kebab-case-id","label":"2-4 word label","definition":"one plain-English sentence","prereq":"id of the single most direct prerequisite concept in this list, or null"}}]"""
    return layout(parse_json(claude(prompt)))


def band(frac: float) -> str:
    """Map a 0..1 position through the batch sequence to a difficulty band."""
    if frac < 0.30:
        return "mostly easy (p~0.72-0.85)"
    if frac < 0.55:
        return "easy-to-medium (p~0.55-0.7)"
    if frac < 0.80:
        return "medium-to-hard (p~0.4-0.55)"
    return "hard (p~0.25-0.4)"


def gen_batch(brief, concepts, frac, seen_stems):
    concept_ids = [c["id"] for c in concepts]
    avoid = "\n".join(f"- {s}" for s in seen_stems[-30:]) or "(none yet)"
    prompt = f"""Write {PER_BATCH} original multiple-choice questions for a professional skill assessment.
Subtopic: {brief}
Difficulty band for THIS batch: {band(frac)} (p = probability a median professional answers correctly).
Tag each question with exactly one concept id from: {concept_ids}
Cover different concepts across the batch. Do NOT duplicate or closely resemble these existing stems:
{avoid}

{RUBRIC}

Return ONLY a JSON array:
[{{"concept":"<id>","stem":"...","options":["...","...","...","..."],"answer":0,
"explanation":"...","grounding":{{"source":"...","note":"..."}},"difficulty_prior":0.6}}]"""
    return parse_json(claude(prompt))


def verify_batch(brief, items):
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
    brief, target = BRIEF[sid], SIZE[sid]
    WORKING.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / f"{sid}.json"

    if out_path.exists():
        data = json.loads(out_path.read_text())
        concepts, items = data["concepts"], data["items"]
        if len(items) >= target:
            print(f"[{sid}] complete ({len(items)}/{target}), skipping", flush=True)
            return
        print(f"[{sid}] extending {len(items)} -> {target}", flush=True)
    else:
        print(f"[{sid}] concepts...", flush=True)
        concepts, items = gen_concepts(brief), []

    seen = [it["stem"][:80] for it in items]
    total_batches = -(-target // PER_BATCH)  # ceil
    while len(items) < target:
        b = len(items) // PER_BATCH
        frac = b / max(1, total_batches - 1)
        print(f"[{sid}] batch {b+1}/{total_batches} draft...", flush=True)
        draft = gen_batch(brief, concepts, frac, seen)
        (WORKING / f"{sid}-b{b}-draft.json").write_text(json.dumps(draft, indent=1))
        print(f"[{sid}] batch {b+1}/{total_batches} verify...", flush=True)
        checked = verify_batch(brief, draft)
        (WORKING / f"{sid}-b{b}-verified.json").write_text(json.dumps(checked, indent=1))
        added = 0
        for q in checked:
            if q.get("verdict") == "keep" and q.get("concept") and len(q.get("options", [])) == 4:
                q.pop("verdict", None)
                q["id"] = f"{sid}-{len(items):03d}"
                q["status"] = "beta"
                items.append(q)
                seen.append(q["stem"][:80])
                added += 1
        # persist incrementally so a kill never loses a completed batch
        json.dump({"id": sid, "concepts": concepts, "items": items,
                   "generated": "claude sonnet draft+verify, pending human review"},
                  open(out_path, "w"), ensure_ascii=False, indent=1)
        if added == 0:  # avoid an infinite loop if a batch fully rejects
            print(f"[{sid}] batch produced 0 keepers; stopping this subtopic", flush=True)
            break
    print(f"[{sid}] DONE: {len(items)} items", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subtopic")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N subtopics this run")
    args = ap.parse_args()
    targets = [s["id"] for s in CATALOG["subtopics"]] if args.all else [args.subtopic]
    done, consecutive_fail = 0, 0
    for sid in targets:
        if args.limit and done >= args.limit:
            print(f"limit {args.limit} reached; stopping run", flush=True)
            break
        try:
            before = (OUT / f"{sid}.json").exists() and len(json.loads((OUT / f"{sid}.json").read_text())["items"]) >= SIZE[sid]
            build_subtopic(sid)
            consecutive_fail = 0
            if not before:
                done += 1
        except Exception as e:
            print(f"[{sid}] FAILED: {e}", flush=True)
            consecutive_fail += 1
            if consecutive_fail >= 3:
                print("3 consecutive failures — likely rate-limited. Stopping; rerun to resume.", flush=True)
                break
