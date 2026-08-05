"""Re-judge saved responses with a different judge. No regeneration.

Judge contamination is the main validity threat for this kind of eval: LLM
judges prefer their own family's writing. Use this to check whether a ranking
survives a judge swap.

    python3 -m readability_eval.rejudge --label gemini-3.5-flash \\
        --judge-model claude-fable-5 --judge-backend hermes --judge-provider anthropic
"""
import argparse
import json
import os
import statistics
from concurrent.futures import ThreadPoolExecutor

from . import judge, lexicon
from .clarity import score_all
from .providers import call
from .run import slop_tax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = {p["id"]: p for p in json.load(
    open(os.path.join(ROOT, "data", "prompts.json")))["prompts"]}


def one(r, jm, jb, jp):
    item = ITEMS[r["id"]]
    try:
        raw = call(jm, judge.build_prompt(item, r["response"]), jb, jp)
        parsed = judge.parse(raw["text"])
    except Exception as e:
        return r["id"], None, str(e)
    return r["id"], parsed, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--judge-model", required=True)
    ap.add_argument("--judge-backend", default="hermes")
    ap.add_argument("--judge-provider", default=None)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()

    src = os.path.join(ROOT, "results", f"{a.label}.json")
    d = json.load(open(src))
    runs = [r for r in d["runs"] if "error" not in r]

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        got = list(ex.map(lambda r: one(r, a.judge_model, a.judge_backend,
                                        a.judge_provider), runs))

    by_id = {i: p for i, p, e in got if p}
    for i, p, e in got:
        if e:
            print(f"  prompt {i}: {e}")

    scores = []
    for r in runs:
        p = by_id.get(r["id"])
        if not p:
            continue
        delivered = sum(1 for x in p.get("facts_delivered", []) if x)
        det, _ = score_all(r["response"], delivered,
                           ITEMS[r["id"]].get("assumed", ()),
                           required=len(ITEMS[r["id"]]["facts"]))
        rules = {**det, **judge.to_scores(p)}
        clarity = statistics.mean(rules.values())
        hits, _ = lexicon.score(r["response"])
        scores.append(clarity * 10 * (1 - slop_tax(hits)))

    orig = d["summary"]["score"]
    new = round(statistics.mean(scores), 1)
    print(f"\n{d['summary']['model']}")
    print(f"  original judge : {orig}")
    print(f"  {a.judge_model:15}: {new}   (n={len(scores)}, delta {new - orig:+.1f})")


if __name__ == "__main__":
    main()
