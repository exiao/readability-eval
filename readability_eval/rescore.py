"""Rescore saved runs after a scoring change. No model calls, no cost.

    python3 -m readability_eval.rescore
"""
import glob
import json
import os
import statistics

from . import lexicon
from .clarity import score_all
from .judge import to_scores
from .run import clarity_score, slop_tax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = {p["id"]: p for p in json.load(
    open(os.path.join(ROOT, "data", "prompts.json")))["prompts"]}


def main():
    for f in sorted(glob.glob(os.path.join(ROOT, "results", "*.json"))):
        d = json.load(open(f))
        if "summary" not in d:
            continue
        for r in d["runs"]:
            if "error" in r:
                continue
            item = ITEMS[r["id"]]
            delivered = sum(1 for x in r["judge"].get("facts_delivered", []) if x)
            det, detail = score_all(r["response"], delivered,
                                    item.get("assumed", ()), required=len(item["asks"]),
                                    budget=item.get("budget"),
                                    audience=item.get("audience", ""))
            rules = {**det, **to_scores(r["judge"])}
            hits, breakdown = lexicon.score(r["response"])
            clarity = clarity_score(rules, detail["economy"].get("coverage"))
            tax = slop_tax(hits)
            r.update(rules=rules, clarity_avg=round(clarity, 2),
                     slop_per_1k=hits, slop_breakdown=breakdown,
                     slop_tax=round(tax, 3), detail=detail,
                     score=round(clarity * 10 * (1 - tax), 1))

        ok = [r for r in d["runs"] if "error" not in r]
        s = d["summary"]
        s["score"] = round(statistics.mean(r["score"] for r in ok), 1)
        s["clarity_avg"] = round(statistics.mean(r["clarity_avg"] for r in ok), 2)
        s["slop_per_1k"] = round(statistics.mean(r["slop_per_1k"] for r in ok), 1)
        s["per_rule"] = {k: round(statistics.mean(r["rules"][k] for r in ok), 2)
                         for k in ok[0]["rules"]}
        json.dump(d, open(f, "w"), indent=1)
        print(f"{s['model']:22} {s['score']}")


if __name__ == "__main__":
    main()
