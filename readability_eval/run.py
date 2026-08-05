"""Run the eval.

  python -m readability_eval.run --model X --backend openrouter
  python -m readability_eval.run --model X --backend hermes --provider anthropic

Score = clarity_avg * (1 - slop_tax), slop_tax capped at 0.30.
"""
import argparse
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from . import judge, lexicon
from .clarity import score_all
from .providers import call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "data", "prompts.json")
RESULTS = os.path.join(ROOT, "results")
SLOP_CEILING = 20.0   # hits/1k that maxes the 30% tax


def slop_tax(hits_per_1k):
    return min(0.30, hits_per_1k / SLOP_CEILING * 0.30)


def eval_one(item, model, backend, provider, judge_model, judge_backend, judge_provider):
    t0 = time.time()
    out = call(model, item["prompt"], backend, provider)
    text = out["text"]
    if not text.strip():
        return {"id": item["id"], "error": "empty response"}

    jraw = call(judge_model, judge.build_prompt(item, text), judge_backend, judge_provider)
    try:
        parsed = judge.parse(jraw["text"])
    except Exception as e:
        return {"id": item["id"], "error": f"judge parse: {e}"}

    delivered = sum(1 for x in parsed.get("facts_delivered", []) if x)
    det, det_detail = score_all(text, delivered, item.get("assumed", ()),
                                required=len(item["facts"]))
    jud = judge.to_scores(parsed)

    rules = {**det, **jud}
    clarity = statistics.mean(rules.values())
    hits, breakdown = lexicon.score(text)
    tax = slop_tax(hits)
    final = round(clarity * 10 * (1 - tax), 1)

    return {
        "id": item["id"], "genre": item["genre"],
        "response": text,
        "rules": rules,
        "clarity_avg": round(clarity, 2),
        "slop_per_1k": hits, "slop_breakdown": breakdown, "slop_tax": round(tax, 3),
        "score": final,
        "facts_delivered": f"{delivered}/{len(item['facts'])}",
        "detail": det_detail, "judge": parsed,
        "shape": lexicon.shape(text),
        "cost_usd": out.get("cost_usd", 0.0) + jraw.get("cost_usd", 0.0),
        "seconds": round(time.time() - t0, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--backend", default="openrouter", choices=["openrouter", "hermes"])
    ap.add_argument("--provider", default=None)
    ap.add_argument("--judge-model", default="google/gemini-3.5-flash")
    ap.add_argument("--judge-backend", default=None)
    ap.add_argument("--judge-provider", default=None)
    ap.add_argument("--label", default=None, help="name for the results file")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jb = a.judge_backend or a.backend

    items = json.load(open(PROMPTS))["prompts"]
    print(f"{a.model} via {a.backend}: {len(items)} prompts, judge={a.judge_model}")

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(lambda it: eval_one(
            it, a.model, a.backend, a.provider,
            a.judge_model, jb, a.judge_provider), items))

    ok = [r for r in rows if "error" not in r]
    errs = [r for r in rows if "error" in r]
    for e in errs:
        print(f"  prompt {e['id']}: {e['error']}", file=sys.stderr)
    if not ok:
        sys.exit("all prompts failed")

    per_rule = {}
    for k in ok[0]["rules"]:
        per_rule[k] = round(statistics.mean(r["rules"][k] for r in ok), 2)

    summary = {
        "model": a.model, "backend": a.backend,
        "n": len(ok), "errors": len(errs),
        "score": round(statistics.mean(r["score"] for r in ok), 1),
        "clarity_avg": round(statistics.mean(r["clarity_avg"] for r in ok), 2),
        "slop_per_1k": round(statistics.mean(r["slop_per_1k"] for r in ok), 1),
        "avg_words": round(statistics.mean(len(r["response"].split()) for r in ok)),
        "per_rule": per_rule,
        "cost_usd": round(sum(r["cost_usd"] for r in ok), 4),
    }

    os.makedirs(RESULTS, exist_ok=True)
    label = a.label or a.model.replace("/", "_").replace(":", "_")
    path = os.path.join(RESULTS, f"{label}.json")
    json.dump({"summary": summary, "runs": rows}, open(path, "w"), indent=1)

    print(json.dumps(summary, indent=1))
    print(f"-> {path}")


if __name__ == "__main__":
    main()
