"""Build the leaderboard table from results/*.json."""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = [("rule1_understandable", "Understand"), ("rule2_economy", "Economy"),
         ("rule3_jargon", "Jargon"), ("rule4_imagery", "Imagery"),
         ("rule5_simple_words", "Simple"), ("rule6_filler", "Filler")]


def load():
    out = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        d = json.load(open(f))
        if "summary" in d:
            out.append(d["summary"])
    return sorted(out, key=lambda s: -s["score"])


def table(rows):
    head = "| # | Model | Score | Clarity | Slop/1k | Words | " + \
           " | ".join(n for _, n in RULES) + " |"
    sep = "|---|---|---:|---:|---:|---:|" + "---:|" * len(RULES)
    lines = [head, sep]
    for i, s in enumerate(rows, 1):
        pr = s["per_rule"]
        cells = " | ".join(f"{pr.get(k, 0):.1f}" for k, _ in RULES)
        lines.append(f"| {i} | `{s['model']}` | **{s['score']}** | "
                     f"{s['clarity_avg']} | {s['slop_per_1k']} | "
                     f"{s['avg_words']} | {cells} |")
    return "\n".join(lines)


if __name__ == "__main__":
    rows = load()
    print(table(rows))
    md = os.path.join(ROOT, "results", "LEADERBOARD.md")
    with open(md, "w") as f:
        f.write("# Leaderboard\n\nScore = clarity x (1 - slop tax). "
                "Each rule 0-10, higher is better.\n\n")
        f.write(table(rows) + "\n")
    print(f"\n-> {md}")
