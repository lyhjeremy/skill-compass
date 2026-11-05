#!/usr/bin/env python3
"""Rebalance which option position holds the answer key in the shipped banks.

The drafting model put 415 of 645 keys at option A. The app shuffles options on
every showing, but the stored order is what anyone reading content/ or using the
API sees. This script:

1. Replaces the explanations listed in scripts/explanation_letter_fixes.json.
   Those named options by letter ("Option D reverses the subtraction"), which
   stops being true once options move; the fixes name the option by content.
2. Refuses to run if any other explanation, stem, option or grounding note still
   names an option by letter or position.
3. Per subtopic, deals key positions A, B, C, D in turn (so the counts differ by
   at most one), shuffles that list, then permutes each item's options so the key
   lands on its assigned position, with the distractors in random order.

Fixed seed, so the output is reproducible. Running it twice gives the same
result as running it once (each run starts from the item's key text, and the
assignment depends only on the item order).

    python3 scripts/rebalance_keys.py           # rewrite content/subtopics/*.json
    python3 scripts/rebalance_keys.py --check   # report only
"""
import collections
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBTOPICS = ROOT / "content" / "subtopics"
FIXES = json.loads((ROOT / "scripts" / "explanation_letter_fixes.json").read_text())
SEED = 20261105

# Option-by-letter or option-by-position wording. Tuned on this bank: formulas
# like P(A|B), "Model B", "column C" and "Hypothesis A" are not matches.
POSITIONAL = re.compile(
    r"\b[Oo]ptions? [A-D]\b"
    r"|\(([A-D])(, [A-D])*\)(?! *[=×x+−-])"
    r"|\b(first|second|third|fourth|last) (option|choice|answer)\b"
    r"|\b(all|none|both) of the above\b"
    r"|\b(above|below) (option|choice|answer)s?\b",
)
FORMULA = re.compile(r"P\([A-D](\|[A-D])?\)|P\([A-D] (and|or) [A-D]\)")


def positional_refs(item):
    fields = [item["stem"], item["explanation"], item["grounding"].get("note", "")] + item["options"]
    hits = []
    for text in fields:
        for m in POSITIONAL.finditer(FORMULA.sub("", text)):
            hits.append(m.group(0))
    return hits


def main(check_only):
    rng = random.Random(SEED)
    fixed, before, after = 0, collections.Counter(), collections.Counter()
    leftovers = []
    for path in sorted(SUBTOPICS.glob("*.json")):
        data = json.loads(path.read_text())
        items = data["items"]
        for it in items:
            if it["id"] in FIXES and it["explanation"] != FIXES[it["id"]]:
                it["explanation"] = FIXES[it["id"]]
                fixed += 1
            if positional_refs(it):
                leftovers.append((it["id"], positional_refs(it)))
            before["ABCD"[it["answer"]]] += 1

        targets = [i % 4 for i in range(len(items))]
        rng.shuffle(targets)
        for it, target in zip(items, targets):
            key = it["options"][it["answer"]]
            distractors = sorted(o for i, o in enumerate(it["options"]) if i != it["answer"])
            rng.shuffle(distractors)
            distractors.insert(target, key)
            assert sorted(distractors) == sorted(it["options"])
            it["options"], it["answer"] = distractors, target
            after["ABCD"[target]] += 1
        if not check_only:
            path.write_text(json.dumps(data, indent=1, ensure_ascii=False))

    if leftovers:
        for iid, hits in leftovers:
            print("positional reference left:", iid, hits)
        sys.exit("fix these in scripts/explanation_letter_fixes.json first")
    print(f"explanations replaced: {fixed} (fix list: {len(FIXES) - 1})")
    print("key positions before:", dict(sorted(before.items())))
    print("key positions after: ", dict(sorted(after.items())))
    if check_only:
        print("--check: nothing written")


if __name__ == "__main__":
    main("--check" in sys.argv)
