"""Run the eval.

  python -m readability_eval.run --model X --backend openrouter
  python -m readability_eval.run --model claude-opus-5 --backend anthropic

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
from .providers import call, probe_contamination

# Judge defaults, per backend. Kept here so `--backend X` alone is runnable
# with one API key and no judge flags.
DEFAULT_JUDGE = {
    "openrouter": "google/gemini-3.5-flash",
    "anthropic": "claude-opus-5",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "data", "prompts.json")
RESULTS = os.path.join(ROOT, "results")
SLOP_CEILING = 20.0   # hits/1k that maxes the 30% tax


def slop_tax(hits_per_1k):
    return min(0.30, hits_per_1k / SLOP_CEILING * 0.30)


def clarity_score(rules):
    """Mean of the six rules, but a near-zero rule caps the whole thing.

    A plain mean lets five 10s carry one 0: an answer that delivered NOTHING
    ("they're different, use whichever fits") averaged 71.7 and landed mid,
    because it was clear, jargon-free and unpadded -- about nothing. Caught by
    the terse_and_empty control.

    Communication is conjunctive. Failing one axis badly is not offset by
    polish elsewhere, so the score is capped at 55 when any rule is under 2.
    """
    vals = list(rules.values())
    mean = statistics.mean(vals)
    return min(mean, 5.5) if min(vals) < 2.0 else mean


# Condition = an instruction appended to every prompt. Lets you separate a
# model property from a prompting artifact: if "answer in 50 words" closes the
# economy gap, the benchmark is measuring default verbosity, not capability.
CONDITIONS = {
    "default": "",
    "brief": "\n\nAnswer in 50 words or less.",
    "short": "\n\nGive a short answer.",
}


def eval_one(item, model, backend, provider, judge_model, judge_backend,
             judge_provider, condition="default", judge_reasoning=None):
    t0 = time.time()
    out = call(model, item["prompt"] + CONDITIONS[condition], backend, provider)
    text = out["text"]
    if not text.strip():
        return {"id": item["id"], "error": "empty response"}

    jraw = call(judge_model, judge.build_prompt(item, text), judge_backend,
                judge_provider, reasoning=judge_reasoning)
    try:
        parsed = judge.parse(jraw["text"])
    except Exception as e:
        return {"id": item["id"], "error": f"judge parse: {e}"}

    delivered = sum(1 for x in parsed.get("facts_delivered", []) if x)
    det, det_detail = score_all(text, delivered, item.get("assumed", ()),
                                required=len(item["asks"]),
                                budget=item.get("budget"))
    jud = judge.to_scores(parsed)

    rules = {**det, **jud}
    clarity = clarity_score(rules)
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
        "facts_delivered": f"{delivered}/{len(item['asks'])}",
        "detail": det_detail, "judge": parsed,
        "shape": lexicon.shape(text),
        "cost_usd": out.get("cost_usd", 0.0) + jraw.get("cost_usd", 0.0),
        "seconds": round(time.time() - t0, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--backend", default="openrouter",
                    choices=["openrouter", "anthropic"])
    ap.add_argument("--provider", default=None)
    ap.add_argument("--judge-model", default=None,
                    help="defaults to a strong model on the selected backend")
    ap.add_argument("--judge-backend", default=None,
                    help="defaults to --backend, so a plain "
                         "`--backend openrouter` run needs no judge flags")
    ap.add_argument("--judge-provider", default=None)
    ap.add_argument("--judge-reasoning", default=None,
                    help="unused; kept for CLI compatibility")
    ap.add_argument("--condition", default="default", choices=list(CONDITIONS),
                    help="instruction appended to every prompt")
    ap.add_argument("--label", default=None, help="name for the results file")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None,
                    help="run only the first N prompts (cheap smoke run). "
                         "Scores from different N are NOT comparable.")
    a = ap.parse_args()

    # The judge follows the subject's backend unless told otherwise, so the
    # documented one-liner works with a single API key. Judging Claude with
    # Claude is the self-preference case the README warns about; pass
    # --judge-model / --judge-backend to cross families.
    jb = a.judge_backend or a.backend
    jm = a.judge_model or DEFAULT_JUDGE[jb]

    items = json.load(open(PROMPTS))["prompts"]
    if a.limit:
        items = items[:a.limit]

    # Contamination gate. Two full runs were thrown away because the backend
    # was silently an agent (tools + persona + memory) rather than a raw
    # model. Never run without this.
    for m, b in {(a.model, a.backend), (jm, jb)}:
        probe_contamination(m, b)
    print(f"backend probe clean: {a.model}/{a.backend}, judge "
          f"{jm}/{jb}")

    print(f"{a.model} via {a.backend}: {len(items)} prompts, judge={jm}")

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(lambda it: eval_one(
            it, a.model, a.backend, a.provider,
            jm, jb, a.judge_provider, a.condition,
            a.judge_reasoning), items))

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
        "model": a.model, "backend": a.backend, "condition": a.condition,
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
