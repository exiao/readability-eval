"""Build the leaderboard table from results/*.json."""
import glob
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = [("rule1_understandable", "Understand"), ("rule2_economy", "Economy"),
         ("rule3_jargon", "Jargon"), ("rule4_imagery", "Imagery"),
         ("rule5_simple_words", "Simple"), ("rule6_filler", "Filler"),
         ("rule7_form", "Form")]


def load(condition="default"):
    """Only one condition per leaderboard; mixing them compares different tests."""
    out = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        d = json.load(open(f))
        s = d.get("summary")
        if s and s.get("condition", "default") == condition:
            out.append(s)
    return sorted(out, key=lambda s: -s["score"])


MEDALS = ["\U0001F947", "\U0001F948", "\U0001F949"]


def table(rows, medals=True):
    """Score first and visually weighted; detail columns trail behind it."""
    head = "| Score | Model | n | Clarity | Slop/1k | Words | " + \
           " | ".join(n for _, n in RULES) + " |"
    sep = "|:---:|---|---:|---:|---:|---:|" + "---:|" * len(RULES)
    lines = [head, sep]
    for i, s in enumerate(rows):
        pr = s["per_rule"]
        cells = " | ".join(f"{pr.get(k, 0):.1f}" for k, _ in RULES)
        medal = MEDALS[i] + " " if medals and i < len(MEDALS) else ""
        lines.append(f"| {medal}**{s['score']}** | `{s['model']}` | {s['n']} | "
                     f"{s['clarity_avg']} | {s['slop_per_1k']} | "
                     f"{s['avg_words']} | {cells} |")
    return "\n".join(lines)


def by_sample_size(rows):
    """Group by n. Scores from different prompt counts are NOT comparable.

    A previous leaderboard silently ranked 12-prompt runs against 24-prompt runs
    and put a partial run in first place. Never merge them into one ranking.
    """
    groups = defaultdict(list)
    for s in rows:
        groups[s["n"]].append(s)
    return sorted(groups.items(), key=lambda kv: -kv[0])


if __name__ == "__main__":
    rows = load()
    groups = by_sample_size(rows)
    md = os.path.join(ROOT, "results", "LEADERBOARD.md")
    parts = ["# Leaderboard\n",
             "Score = clarity x (1 - slop tax). Each rule 0-10, higher is "
             "better. Prompts are real ChatGPT conversations sampled from "
             "WildChat-1M; see README for the sampling method.\n"]
    for n, gr in groups:
        gr = sorted(gr, key=lambda s: -s["score"])
        if n >= 30:
            parts.append(f"\n## Full run ({n} prompts)\n")
            parts.append(table(gr))
        else:
            parts.append(f"\n## Smoke sample ({n} prompts) — NOT comparable "
                         f"to the full run\n\nToo few prompts to rank. Treat "
                         f"gaps under ~5 points as noise.\n")
            parts.append(table(gr, medals=False))
        parts.append("")
    out = "\n".join(parts)
    print(out)
    with open(md, "w") as f:
        f.write(out)
    print(f"\n-> {md}")
