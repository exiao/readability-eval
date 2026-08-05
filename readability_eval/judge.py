"""Judge for rules 1 (easy to understand) and 4 (imagery), plus fact delivery.

The judge emits ordered LABELS, never numbers, and must quote the offending
sentence. No quote means no penalty — this stops the judge inventing vague
complaints, which is the main failure mode of LLM-as-judge setups.

Fact delivery is judged too, because rule 2 needs a denominator. A regex cannot
tell whether "you should probably restart things" delivers "mentions restart
requirement"; a judge can.
"""
import json
import re

LABELS_CLARITY = {"clear": 10, "needs_a_reread": 5, "opaque": 0}
LABELS_IMAGERY = {"concrete": 10, "abstract_but_fine": 7, "needed_an_image": 3}

TEMPLATE = """You are grading ONE response for readability. Be strict and literal.

AUDIENCE: {audience}

THE PROMPT THEY ANSWERED:
{prompt}

REQUIRED FACTS (did the response deliver each one?):
{facts}

THE RESPONSE:
---
{response}
---

Return ONLY valid JSON, no prose, no code fence:

{{
  "facts_delivered": [true/false for each required fact, in order],
  "clarity": "clear" | "needs_a_reread" | "opaque",
  "clarity_quote": "the exact sentence that is hardest to understand, or empty string if none",
  "imagery": "concrete" | "abstract_but_fine" | "needed_an_image",
  "imagery_quote": "the exact abstract sentence that needed a concrete image, or empty string if none",
  "imagery_suggestion": "the concrete image or example you would have used, or empty string"
}}

Rules for grading:
- Judge clarity FOR THE STATED AUDIENCE. A precise technical term a backend
  engineer knows is not a clarity problem. Replacing it with vague everyday
  words would be worse.
- "clear" means a competent member of that audience gets it on one read.
- Only say "needed_an_image" if the text explains a relationship, process, or
  comparison in pure abstraction AND you can name the concrete image that fixes
  it. If you cannot name one, answer "abstract_but_fine".
- A fact counts as delivered if the meaning is present, even if worded
  differently. It does not count if only gestured at vaguely.
"""


def build_prompt(item, response):
    facts = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(item["facts"]))
    return TEMPLATE.format(audience=item["audience"], prompt=item["prompt"],
                           facts=facts, response=response)


def parse(raw):
    """Tolerant JSON extraction — judges wrap output in fences despite instructions."""
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"no JSON in judge output: {raw[:200]}")
    return json.loads(m.group(0))


def to_scores(parsed):
    """Labels -> numbers. Quote required, else the penalty is dropped."""
    clarity = LABELS_CLARITY.get(parsed.get("clarity"), 5)
    if clarity < 10 and not (parsed.get("clarity_quote") or "").strip():
        clarity = 10  # unsubstantiated complaint
    imagery = LABELS_IMAGERY.get(parsed.get("imagery"), 7)
    if imagery < 7 and not (parsed.get("imagery_suggestion") or "").strip():
        imagery = 7   # could not name the image it wanted
    return {"rule1_understandable": float(clarity), "rule4_imagery": float(imagery)}
