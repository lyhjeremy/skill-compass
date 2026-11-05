#!/usr/bin/env python3
"""Measure what the independent review pass changed in the question banks.

Inputs: content/_working/<subtopic>-b<N>-draft.json (the drafting pass) and the
matching -verified.json (the review pass). Those working files are gitignored;
the shipped banks in content/subtopics/ are the verified items. Questions are
paired by position within a batch (the concept ids match on every pair).

Also checks two properties of the shipped banks that a test-taker could exploit:
how often the correct option is the uniquely longest one, and which letter holds
the key (the app shows options in stored order).

    python3 eval/review_pass.py     # writes eval/review_pass.json
"""
import collections
import glob
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W = ROOT / "content" / "_working"
FIELDS = ["stem", "options", "answer", "explanation", "grounding", "difficulty_prior"]


def longest_is_key(q):
    lens = [len(o) for o in q["options"]]
    return lens[q["answer"]] == max(lens) and lens.count(max(lens)) == 1


def main():
    pairs, unreviewed = [], []
    for df in sorted(glob.glob(str(W / "*-draft.json"))):
        vf = df.replace("-draft.json", "-verified.json")
        if not os.path.exists(vf):
            unreviewed.append((os.path.basename(df), len(json.load(open(df)))))
            continue
        d, v = json.load(open(df)), json.load(open(vf))
        assert len(d) == len(v), df
        for a, b in zip(d, v):
            assert a["concept"] == b["concept"], df
            pairs.append((os.path.basename(vf), a, b))

    types = {
        "correct_option_reworded": lambda a, b: a["options"][a["answer"]] != b["options"][b["answer"]],
        "distractors_only_rewritten": lambda a, b: a["options"] != b["options"]
            and a["options"][a["answer"]] == b["options"][b["answer"]],
        "stem_rewritten": lambda a, b: a["stem"] != b["stem"],
        "source_replaced": lambda a, b: a["grounding"]["source"] != b["grounding"]["source"],
        "difficulty_prior_changed": lambda a, b: a["difficulty_prior"] != b["difficulty_prior"],
        "explanation_rewritten": lambda a, b: a["explanation"] != b["explanation"],
        "answer_index_changed": lambda a, b: a["answer"] != b["answer"],
    }
    counts = collections.Counter()
    examples = {}
    for f, a, b in pairs:
        if any(a[k] != b[k] for k in FIELDS):
            counts["any_change"] += 1
        if any(a[k] != b[k] for k in ("stem", "options", "answer")):
            counts["question_text_changed"] += 1
        for name, test in types.items():
            if test(a, b):
                counts[name] += 1
                examples.setdefault(name, {"file": f, "concept": a["concept"], "draft": a, "verified": b})

    shift = [b["difficulty_prior"] - a["difficulty_prior"] for _, a, b in pairs
             if a["difficulty_prior"] != b["difficulty_prior"]]

    shipped = []
    for f in sorted((ROOT / "content" / "subtopics").glob("*.json")):
        for q in json.load(open(f))["items"]:
            shipped.append((f.stem, q))
    key_pos = collections.Counter("ABCD"[q["answer"]] for _, q in shipped)
    per_sub = collections.defaultdict(collections.Counter)
    for s, q in shipped:
        per_sub[s]["ABCD"[q["answer"]]] += 1

    out = {
        "drafted": len(pairs) + sum(n for _, n in unreviewed),
        "reviewed": len(pairs),
        "unreviewed_batches": unreviewed,
        "shipped": len(shipped),
        "change_counts": dict(sorted(counts.items())),
        "prior_shift": {"n": len(shift), "raised": sum(s > 0 for s in shift),
                        "lowered": sum(s < 0 for s in shift),
                        "median_abs": round(sorted(abs(s) for s in shift)[len(shift) // 2], 3),
                        "max_abs": round(max(abs(s) for s in shift), 3)},
        "longest_option_is_key": {"draft": sum(longest_is_key(a) for _, a, _ in pairs),
                                  "verified": sum(longest_is_key(b) for _, _, b in pairs),
                                  "shipped": sum(longest_is_key(q) for _, q in shipped)},
        "shipped_key_position": dict(sorted(key_pos.items())),
        "subtopics_with_majority_A": sum(c["A"] * 2 > sum(c.values()) for c in per_sub.values()),
        "subtopics": len(per_sub),
        "per_subtopic_key_position": {s: dict(sorted(c.items())) for s, c in sorted(per_sub.items())},
        "examples": examples,
    }
    path = ROOT / "eval" / "review_pass.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("examples", "per_subtopic_key_position")}, indent=1))
    print("wrote", path)


if __name__ == "__main__":
    main()
