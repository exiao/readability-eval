"""Iterative eval: does a model's writing degrade when it edits its own text?

Applies SlopCodeBench (arXiv 2603.24755) to prose. The paper's finding is that
single-shot benchmarks systematically undermeasure the failure that matters:
agents pass the test at every step while the artifact rots underneath them.
Every other run in this repo is single-shot, so it cannot see that at all.

Each problem is a chain of checkpoints. At C1 the model writes from scratch.
At C2+ it receives ITS OWN previous answer plus one new requirement, and must
produce the whole document again. Requirements accumulate, so `asks` and the
word budget grow with the spec and growth alone is never scored as a defect.

    python3 -m readability_eval.iterate --model claude-opus-5 \
        --backend anthropic

Reported per checkpoint: the normal readability score, plus erosion and
verbosity. The headline is the DRIFT of those two, not their level.
"""
import argparse
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from . import judge, lexicon, metrics
from .clarity import score_all
from .providers import call, probe_contamination
from .run import DEFAULT_JUDGE, cap_scaffold, clarity_score, slop_tax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBLEMS = os.path.join(ROOT, "data", "checkpoints.json")
RESULTS = os.path.join(ROOT, "results", "iterative")

EXTEND = """Here is the current version of the document:

<document>
{prior}
</document>

New requirement: {spec}

Rewrite the document so it satisfies the new requirement along with everything
it already covers. Return only the document."""


def score_text(text, item):
    """Same scorer as the single-shot run, so numbers are comparable."""
    jraw = call(item["_jm"], judge.build_prompt(item, text), item["_jb"],
                item["_jp"])
    parsed = judge.parse(jraw["text"])
    delivered = sum(1 for x in parsed.get("facts_delivered", []) if x)
    det, det_detail = score_all(text, delivered, item.get("assumed", ()),
                                required=len(item["asks"]),
                                budget=item.get("budget"),
                                audience=item.get("audience", ""))
    jud = judge.to_scores(parsed)
    jud, _ = cap_scaffold(jud, text, item.get("budget") or 300)
    det, jud = judge.merge_judged(det, jud)
    rules = {**det, **jud}
    clarity = clarity_score(rules, det_detail["economy"].get("coverage"))
    hits, breakdown = lexicon.score(text)
    return {
        "rules": rules,
        "clarity_avg": round(clarity, 2),
        "slop_per_1k": hits,
        "score": round(clarity * 10 * (1 - slop_tax(hits)), 1),
        "facts_delivered": f"{delivered}/{len(item['asks'])}",
        "cost_usd": jraw.get("cost_usd", 0.0),
    }


def run_problem(prob, model, backend, provider, jm, jb, jp, reasoning=None):
    """One trajectory. Sequential by necessity: Cn+1 needs Cn's output."""
    rows, prior, asks = [], None, []
    for i, cp in enumerate(prob["checkpoints"], 1):
        asks = asks + cp["asks"]          # requirements accumulate
        prompt = cp["spec"] if prior is None else EXTEND.format(
            prior=prior, spec=cp["spec"])
        t0 = time.time()
        try:
            out = call(model, prompt, backend, provider, reasoning=reasoning)
        except Exception as e:
            rows.append({"checkpoint": i, "error": f"model call: {e}"})
            break                          # the chain cannot continue
        text = out["text"]
        if not text.strip():
            rows.append({"checkpoint": i, "error": "empty response"})
            break

        item = {"id": f"{prob['id']}#{i}", "genre": prob["genre"],
                "prompt": cp["spec"], "audience": prob["audience"],
                "asks": asks, "assumed": prob.get("assumed", ()),
                "budget": cp.get("budget"),
                "_jm": jm, "_jb": jb, "_jp": jp}
        try:
            sc = score_text(text, item)
        except Exception as e:
            rows.append({"checkpoint": i, "error": f"judge: {e}"})
            break

        row = {"checkpoint": i, "spec": cp["spec"], "response": text,
               "words": len(text.split()), "budget": cp.get("budget"),
               **sc, **metrics.measure(text),
               "seconds": round(time.time() - t0, 1)}
        row["cost_usd"] = round(row["cost_usd"] + out.get("cost_usd", 0.0), 5)
        rows.append(row)
        prior = text
    return {"problem": prob["id"], "genre": prob["genre"],
            "expected_checkpoints": len(prob["checkpoints"]),
            "checkpoints": rows}


def summarise(trajectories):
    eros, verb, scores = [], [], []
    truncated = 0
    for t in trajectories:
        ok = [c for c in t["checkpoints"] if "error" not in c]
        # A trajectory that died at C3 still has >= 2 checkpoints, so a length
        # check alone counted a truncated chain as complete and let its early
        # endpoint into every headline drift number. Require the FULL chain.
        expected = t.get("expected_checkpoints", len(t["checkpoints"]))
        if len(ok) < expected:
            truncated += 1
            continue
        if len(ok) >= 2:
            eros.append(metrics.trend([c["erosion"] for c in ok]))
            verb.append(metrics.trend([c["verbosity"] for c in ok]))
            scores.append(metrics.trend([c["score"] for c in ok]))
    if not eros:
        return {"complete_trajectories": 0, "truncated_trajectories": truncated}
    return {
        "complete_trajectories": len(eros),
        "truncated_trajectories": truncated,
        # The paper's headline numbers, in the paper's own form.
        "erosion_drift": round(statistics.mean(eros), 4),
        "verbosity_drift": round(statistics.mean(verb), 4),
        "score_drift": round(statistics.mean(scores), 2),
        "pct_erosion_rising": round(100 * sum(x > 0 for x in eros) / len(eros)),
        "pct_verbosity_rising": round(100 * sum(x > 0 for x in verb) / len(verb)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--backend", default="openrouter",
                    choices=["openrouter", "anthropic"])
    ap.add_argument("--provider", default=None)
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--judge-backend", default=None)
    ap.add_argument("--judge-provider", default=None)
    ap.add_argument("--reasoning", default=None,
                    choices=["low", "medium", "high"])
    ap.add_argument("--label", default=None)
    ap.add_argument("--limit", type=int, default=None,
                    help="run only the first N problems")
    ap.add_argument("--workers", type=int, default=2,
                    help="problems in parallel; checkpoints are always serial")
    ap.add_argument("--skip-probe", action="store_true")
    a = ap.parse_args()

    jb = a.judge_backend or a.backend
    jm = a.judge_model or DEFAULT_JUDGE[jb]

    probs = json.load(open(PROBLEMS))["problems"]
    if a.limit:
        probs = probs[:a.limit]

    if not a.skip_probe:
        for m, b in {(a.model, a.backend), (jm, jb)}:
            probe_contamination(m, b)
        print(f"backend probe clean: {a.model}/{a.backend}, judge {jm}/{jb}")

    n_cp = sum(len(p["checkpoints"]) for p in probs)
    print(f"{a.model} via {a.backend}: {len(probs)} problems, "
          f"{n_cp} checkpoints, judge={jm}")

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        trajs = list(ex.map(lambda p: run_problem(
            p, a.model, a.backend, a.provider, jm, jb, a.judge_provider,
            a.reasoning), probs))

    for t in trajs:
        for c in t["checkpoints"]:
            if "error" in c:
                print(f"  {t['problem']} C{c['checkpoint']}: {c['error']}",
                      file=sys.stderr)

    summary = {"model": a.model, "backend": a.backend, "judge_model": jm,
               "judge_backend": jb, "problems": len(trajs), **summarise(trajs)}
    if not summary.get("complete_trajectories"):
        sys.exit("no trajectory produced two or more checkpoints")

    os.makedirs(RESULTS, exist_ok=True)
    label = a.label or a.model.replace("/", "_").replace(":", "_")
    path = os.path.join(RESULTS, f"{label}.json")
    json.dump({"summary": summary, "trajectories": trajs},
              open(path, "w"), indent=1)

    for t in trajs:
        ok = [c for c in t["checkpoints"] if "error" not in c]
        print(f"\n{t['problem']}")
        for c in ok:
            print(f"  C{c['checkpoint']}  score {c['score']:5.1f}  "
                  f"erosion {c['erosion']:.3f}  verbosity {c['verbosity']:.3f}"
                  f"  {c['words']}w/{c['budget']}  {c['facts_delivered']}")
    print("\n" + json.dumps(summary, indent=1))
    print(f"-> {path}")


if __name__ == "__main__":
    main()
