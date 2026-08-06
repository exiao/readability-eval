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
from .run import clarity_score, slop_tax

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
    ap.add_argument("--write", action="store_true",
                    help="save the new judge output and scores back to the "
                         "results file. Required after adding a rule: rescore "
                         "reuses saved judge dicts, so a new judged axis would "
                         "silently default for every model.")
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
        det, detail = score_all(r["response"], delivered,
                                ITEMS[r["id"]].get("assumed", ()),
                                required=len(ITEMS[r["id"]]["asks"]),
                                budget=ITEMS[r["id"]].get("budget"))
        rules = {**det, **judge.to_scores(p)}
        clarity = clarity_score(rules)
        hits, breakdown = lexicon.score(r["response"])
        tax = slop_tax(hits)
        score = clarity * 10 * (1 - tax)
        scores.append(score)
        if a.write:
            r.update(judge=p, rules=rules, clarity_avg=round(clarity, 2),
                     slop_per_1k=hits, slop_breakdown=breakdown,
                     slop_tax=round(tax, 3), detail=detail,
                     facts_delivered=f"{delivered}/{len(ITEMS[r['id']]['asks'])}",
                     score=round(score, 1))

    orig = d["summary"]["score"]
    new = round(statistics.mean(scores), 1)
    print(f"\n{d['summary']['model']}")
    print(f"  original judge : {orig}")
    print(f"  {a.judge_model:15}: {new}   (n={len(scores)}, delta {new - orig:+.1f})")

    if a.write:
        ok = [r for r in runs if r["id"] in by_id]
        s = d["summary"]
        s["score"] = new
        s["judge_model"] = a.judge_model
        s["clarity_avg"] = round(statistics.mean(r["clarity_avg"] for r in ok), 2)
        s["slop_per_1k"] = round(statistics.mean(r["slop_per_1k"] for r in ok), 1)
        s["per_rule"] = {k: round(statistics.mean(r["rules"][k] for r in ok), 2)
                         for k in ok[0]["rules"]}
        json.dump(d, open(src, "w"), indent=1)
        print(f"  -> wrote {src}")


if __name__ == "__main__":
    main()
