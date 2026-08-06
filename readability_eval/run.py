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

from . import judge, lexicon, scaffold
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


# Economy is weighted below the other rules. It is the only rule with real
# variance, so at equal weight it silently became the benchmark: 81% of saved
# answers scored HIGHER when truncated to half their length, some by 42 points.
# Truncation cannot improve an answer, so any metric that rewards it is
# measuring the wrong thing. Being long is a real defect, but a smaller one
# than being unclear or wrong, and it is the defect a reader can skim past.
# 0.75 rather than 0.5. At 0.5 a 2577-word answer to a 524-word question
# scored 90.6 against a 95.1 winner, which is not a 4 point defect. At 1.0 the
# truncation exploit is still worth +5.7. 0.75 keeps the worst gain from
# halving an answer at +4.4 while a 5x-over answer still loses ~7 points.
RULE_WEIGHTS = {"rule2_economy": 0.75}
DEFAULT_RULE_WEIGHT = 1.0

# Rules where a near-zero score means the answer failed, not that it was
# merely bloated.
CONJUNCTIVE = ("rule1_understandable", "rule3_jargon", "rule5_simple_words",
               "rule6_filler", "rule7_form")


def clarity_score(rules, coverage=None):
    """Weighted mean, with a cap when a rule that matters bottoms out.

    A plain mean lets five 10s carry one 0: an answer that delivered NOTHING
    ("they're different, use whichever fits") averaged 71.7 and landed mid,
    because it was clear, jargon-free and unpadded -- about nothing. Caught by
    the terse_and_empty control.

    Communication is conjunctive, so a rule under 2 still caps the score at 55.

    Economy is deliberately NOT one of those rules, because it conflates two
    different failures. It multiplies length against coverage, so it reads 0.0
    both for an answer that said nothing and for one that answered fully at
    great length. Capping on it punished those identically: 15 of the 19 caps
    in the saved corpus were verbosity, costing ~31 points each.

    The empty case is caught by `coverage` instead, which is the half of
    economy that actually means failure. Answering under a third of what was
    asked caps the score however clean the prose is.
    """
    num = sum(v * RULE_WEIGHTS.get(k, DEFAULT_RULE_WEIGHT)
              for k, v in rules.items())
    den = sum(RULE_WEIGHTS.get(k, DEFAULT_RULE_WEIGHT) for k in rules)
    mean = num / den
    floor = min((v for k, v in rules.items() if k in CONJUNCTIVE), default=10.0)
    if floor < 2.0 or (coverage is not None and coverage < 0.34):
        return min(mean, 5.5)
    return mean


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

    # Rule 7, deterministic half. The judge grades form subjectively and is
    # forgiving: it quotes one bad heading and calls the rest fine. Scaffolding
    # density catches what it waves through -- 14 responses in the v3 corpus
    # scored a perfect 10 on form while carrying up to 69 headings and 134 list
    # items. Cap rather than average, so the judge can still fail an answer the
    # counter thinks is fine, but cannot pass one it doesn't.
    scaf, scaf_detail = scaffold.score(text, item.get("budget") or 300)
    jud["rule7_form"] = min(jud["rule7_form"], scaf)

    rules = {**det, **jud}
    clarity = clarity_score(rules, det_detail["economy"].get("coverage"))
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
        "detail": det_detail, "judge": parsed, "scaffold": scaf_detail,
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
