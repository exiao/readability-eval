"""Deterministic scaffolding density.

Rule 7 asks whether an answer is shaped like the answer or like a report. The
judge does that subjectively and must quote the heading it objects to, which
makes it precise but also forgiving: it quotes one bad heading and moves on.

This module measures the other half mechanically. A 60-word question answered
with 90 headings and 216 bullets is not a stylistic quibble, it is a report
delivered instead of an answer, and it should not depend on a judge noticing.

Density is measured against the prompt's word budget, not the response length.
Scoring against its own length is circular: a 2500-word answer with 90 headings
looks "normally structured" for its size, which is exactly the failure.
"""
import re

# Per 100 budget words. Calibrated on 265 real responses: the median answer
# sits near 2 headings and 5 list items per 100 budget words, so these
# thresholds fire on genuine outliers rather than ordinary structure.
HEAD_FREE = 3.0
LIST_FREE = 8.0
HEAD_MAX = 12.0
LIST_MAX = 30.0

BOLD_LABEL = re.compile(r"^\s*\*\*[^*]{1,60}\*\*:?\s*$")
MD_HEAD = re.compile(r"^\s{0,3}#{1,6}\s+\S")
BULLET = re.compile(r"^\s*([-*+]|\d{1,2}[.)])\s+\S")


def _strip_code(text):
    return re.sub(r"```.*?```", "", text, flags=re.S)


def count(text):
    """Headings, standalone bold labels, and list items outside code fences."""
    lines = _strip_code(text).split("\n")
    heads = sum(1 for l in lines if MD_HEAD.match(l) or BOLD_LABEL.match(l))
    lists = sum(1 for l in lines if BULLET.match(l))
    return heads, lists


def density(text, budget):
    """Scaffolding per 100 budget words."""
    b = max(1, budget) / 100.0
    h, l = count(text)
    return {"headings": h, "list_items": l,
            "headings_per_100b": round(h / b, 2),
            "list_items_per_100b": round(l / b, 2)}


def score(text, budget):
    """0-10. 10 until scaffolding clearly exceeds what the ask can justify.

    Returns (score, detail). Under the free allowance costs nothing, so a
    genuinely list-shaped answer to a list-shaped question is not punished.
    """
    d = density(text, budget)
    h, l = d["headings_per_100b"], d["list_items_per_100b"]
    hp = 0.0 if h <= HEAD_FREE else min(1.0, (h - HEAD_FREE) / (HEAD_MAX - HEAD_FREE))
    lp = 0.0 if l <= LIST_FREE else min(1.0, (l - LIST_FREE) / (LIST_MAX - LIST_FREE))
    penalty = max(hp, lp)          # worst offender, not the sum
    d["scaffold_score"] = round(10.0 * (1.0 - penalty), 1)
    return d["scaffold_score"], d
