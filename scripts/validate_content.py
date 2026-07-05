#!/usr/bin/env python3
"""Structural validator for SkillCompass content (run in CI + before commit).

Checks every subtopic JSON against the item schema and the mechanical parts of
the rubric. Semantic quality (is the answer actually right?) stays with the
verify pass + human review.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors, warnings = [], []


def check_subtopic(path: Path):
    data = json.loads(path.read_text())
    sid = data["id"]
    concept_ids = {c["id"] for c in data["concepts"]}
    if not (6 <= len(data["concepts"]) <= 12):
        errors.append(f"{sid}: {len(data['concepts'])} concepts (want 6-12)")
    for c in data["concepts"]:
        if c.get("prereq") and c["prereq"] not in concept_ids:
            errors.append(f"{sid}/{c['id']}: prereq '{c['prereq']}' not in concept list")
        if not all(k in c for k in ("label", "definition", "x", "y")):
            errors.append(f"{sid}/{c['id']}: missing concept fields")

    stems = set()
    if len(data["items"]) < 8:
        warnings.append(f"{sid}: only {len(data['items'])} items (thin pool for retakes)")
    for it in data["items"]:
        iid = it.get("id", "?")
        if it.get("concept") not in concept_ids:
            errors.append(f"{iid}: concept '{it.get('concept')}' not in concept list")
        if len(it.get("options", [])) != 4:
            errors.append(f"{iid}: {len(it.get('options', []))} options")
        if not (0 <= it.get("answer", -1) <= 3):
            errors.append(f"{iid}: bad answer index")
        if not (0.1 <= it.get("difficulty_prior", 0) <= 0.95):
            errors.append(f"{iid}: difficulty_prior {it.get('difficulty_prior')}")
        if len(it.get("stem", "").split()) > 55:
            warnings.append(f"{iid}: stem {len(it['stem'].split())} words (rubric: <=45)")
        opts = it.get("options", [])
        if opts and max(map(len, opts)) == len(opts[it.get("answer", 0)]) and len(opts[it["answer"]]) > 1.6 * min(map(len, opts)):
            warnings.append(f"{iid}: correct answer is much longer than distractors")
        key = it.get("stem", "")[:70].lower()
        if key in stems:
            errors.append(f"{iid}: near-duplicate stem")
        stems.add(key)
        if not it.get("explanation") or not it.get("grounding", {}).get("source"):
            errors.append(f"{iid}: missing explanation/grounding")
    covered = {it["concept"] for it in data["items"]}
    missing = concept_ids - covered
    if missing:
        warnings.append(f"{sid}: no items for concepts {sorted(missing)}")
    print(f"  {sid}: {len(data['items'])} items, {len(data['concepts'])} concepts")


if __name__ == "__main__":
    files = sorted((ROOT / "content" / "subtopics").glob("*.json"))
    print(f"validating {len(files)} subtopic files")
    for f in files:
        check_subtopic(f)
    for w in warnings:
        print(f"  WARN {w}")
    for e in errors:
        print(f"  ERROR {e}")
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)
