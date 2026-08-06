"""Score the scorer against hand-written controls with known verdicts.

    python3 -m readability_eval.selftest                 # deterministic only
    python3 -m readability_eval.selftest --judge MODEL   # full pipeline

Without --judge this exercises rules 2/3/5/6 and the slop lexicon using the
control's own fact count, which is enough to catch most scoring regressions and
costs nothing. With --judge it runs the real pipeline end to end.

Bands: low < 70 <= mid < 85 <= high.
"""
import argparse
import json
import os
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from . import judge, lexicon
from .clarity import score_all
from .providers import call
from .run import clarity_score, slop_tax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = {p["id"]: p for p in json.load(
    open(os.path.join(ROOT, "data", "prompts.json")))["prompts"]}
_CTL = json.load(open(os.path.join(ROOT, "data", "controls.json")))
CONTROLS = _CTL["cases"]
PAIRS = _CTL.get("pairs", [])

LOW, HIGH = 70.0, 85.0


def band(score):
    return "low" if score < LOW else ("mid" if score < HIGH else "high")


def score_case(c, judge_model=None, backend="openrouter", provider=None):
    # Each control embeds the prompt it answers. They used to reference
    # prompts.json by id, and when that file was re-numbered every control
    # began grading its answer against an unrelated question: the judge
    # returned 0/4 facts on all 17, economy collapsed to 0.0 through the
    # coverage multiplier, and the suite reported failures that had nothing to
    # do with the scorer. A fixture that can drift is not a fixture.
    item = c.get("item") or ITEMS[c["prompt_id"]]
    text = c["text"]

    if judge_model:
        raw = call(judge_model, judge.build_prompt(item, text), backend, provider)
        parsed = judge.parse(raw["text"])
        delivered = sum(1 for x in parsed.get("facts_delivered", []) if x)
        jud = judge.to_scores(parsed)
    else:
        # No judge: assume all facts land and both judged rules are perfect.
        # This is deliberately GENEROUS, so a control that still lands in "low"
        # failed on deterministic grounds alone.
        delivered = len(item["asks"])
        jud = {"rule1_understandable": 10.0, "rule4_imagery": 10.0,
               "rule7_form": 10.0}

    det, detail = score_all(text, delivered, item.get("assumed", ()), budget=item.get("budget"),
                            required=len(item["asks"]))
    rules = {**det, **jud}
    hits, breakdown = lexicon.score(text)
    clarity = clarity_score(rules, detail["economy"].get("coverage"))
    return round(clarity * 10 * (1 - slop_tax(hits)), 1), hits, breakdown, rules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default=None, help="run the real judge too")
    ap.add_argument("--backend", default="openrouter",
                    choices=["openrouter", "anthropic"])
    ap.add_argument("--provider", default=None)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    if a.judge:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            got = list(ex.map(lambda c: score_case(c, a.judge, a.backend,
                                                   a.provider), CONTROLS))
    else:
        got = [score_case(c) for c in CONTROLS]

    fails = []
    print(f"{'case':26} {'want':>5} {'got':>5} {'score':>6} {'slop':>6}")
    print("-" * 56)
    for c, (score, hits, breakdown, rules) in zip(CONTROLS, got):
        actual = band(score)
        ok = actual == c["expect"]
        mark = " " if ok else "X"
        print(f"{mark} {c['name']:24} {c['expect']:>5} {actual:>5} "
              f"{score:>6} {hits:>6}")
        if not ok:
            fails.append((c, score, actual, breakdown, rules))

    # Pairwise checks. Absolute bands drift with judge and prompt wording;
    # "A must beat B" is the assertion that actually has to hold.
    scores = {c["name"]: s for c, (s, _, _, _) in zip(CONTROLS, got)}
    pair_fails = []
    print()
    for better, worse, why in PAIRS:
        hi, lo = scores.get(better), scores.get(worse)
        if hi is None or lo is None:
            continue
        ok = hi > lo
        print(f"{' ' if ok else 'X'} {better} > {worse}   "
              f"{hi} vs {lo}   {why}")
        if not ok:
            pair_fails.append((better, worse, hi, lo, why))

    print()
    if pair_fails:
        print(f"{len(pair_fails)} PAIR CHECKS FAILED")
        for b, w, hi, lo, why in pair_fails:
            print(f"  {b} ({hi}) should beat {w} ({lo}): {why}")
        print()

    if fails or pair_fails:
        if not fails:
            sys.exit(1)
    if fails:
        print(f"{len(fails)}/{len(CONTROLS)} FAILED\n")
        for c, score, actual, breakdown, rules in fails:
            print(f"  {c['name']}: wanted {c['expect']}, got {actual} ({score})")
            print(f"    why it matters: {c['why']}")
            print(f"    rules: { {k: v for k, v in rules.items()} }")
            print(f"    slop:  {breakdown}\n")
        sys.exit(1)
    print(f"all {len(CONTROLS)} controls pass")


if __name__ == "__main__":
    main()
