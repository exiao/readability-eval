"""Build the leaderboard table from results/*.json."""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = [("rule1_understandable", "Understand"), ("rule2_economy", "Economy"),
         ("rule3_jargon", "Jargon"), ("rule4_imagery", "Imagery"),
         ("rule5_simple_words", "Simple"), ("rule6_filler", "Filler")]


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


def table(rows):
    """Score first and visually weighted; detail columns trail behind it."""
    head = "| Score | Model | Clarity | Slop/1k | Words | " + \
           " | ".join(n for _, n in RULES) + " |"
    sep = "|:---:|---|---:|---:|---:|" + "---:|" * len(RULES)
    lines = [head, sep]
    for i, s in enumerate(rows):
        pr = s["per_rule"]
        cells = " | ".join(f"{pr.get(k, 0):.1f}" for k, _ in RULES)
        medal = MEDALS[i] + " " if i < len(MEDALS) else ""
        lines.append(f"| {medal}**{s['score']}** | `{s['model']}` | "
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
        f.write(table(rows) + "\n\n![scores](chart.png)\n")
    print(f"\n-> {md}")
