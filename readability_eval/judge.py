"""Judge for rules 1 (understand), 4 (imagery) and 7 (form), plus fact delivery.

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
# Rule 7: structural theater. The lexicon cannot see this — scaffolding is made
# of headers, tables and section labels, not tic phrases, so a report-shaped
# answer to a four-fact question scored 88/100 with zero slop hits
# (council_report_slop control). Judged, because whether a heading earns its
# place depends on what was asked.
LABELS_FORM = {"fits": 10, "some_scaffolding": 5, "report_theater": 0}

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

BEFORE GRADING: if the prompt asked for a bare data format (JSON, CSV, a single
value) and the response is exactly that payload with nothing around it, then the
response is CORRECT AND COMPLETE. Every fact whose content appears anywhere in
the payload is delivered — read the keys and values, not the prose around them.
Grade it "clear", "concrete" and "fits", and stop looking for defects. Absence
of prose is what was ordered, not a failure.

Return ONLY valid JSON, no prose, no code fence:

{{
  "facts_delivered": [true/false for each required fact, in order],
  "clarity": "clear" | "needs_a_reread" | "opaque",
  "clarity_quote": "the exact sentence that is hardest to understand, or empty string if none",
  "imagery": "concrete" | "abstract_but_fine" | "needed_an_image",
  "imagery_quote": "the exact abstract sentence that needed a concrete image, or empty string if none",
  "imagery_suggestion": "the concrete image or example you would have used, or empty string",
  "form": "fits" | "some_scaffolding" | "report_theater",
  "form_quote": "the exact heading, label or table row that is doing no work, or empty string if none"
}}

Rules for grading:
- Judge clarity FOR THE STATED AUDIENCE. A precise technical term a backend
  engineer knows is not a clarity problem. Replacing it with vague everyday
  words would be worse.
- "clear" means a competent member of that audience gets it on one read.
- When the audience is a machine or a script and the prompt asked for a data
  format (JSON, CSV, a single value), a bare well-formed payload is "clear" and
  its form "fits". Do not mark it opaque for lacking sentences, and do not
  demand explanation the prompt forbade.
- Only say "needed_an_image" if the text explains a relationship, process, or
  comparison in pure abstraction AND you can name the concrete image that fixes
  it. If you cannot name one, answer "abstract_but_fine".
- A fact counts as delivered if the meaning is present, even if worded
  differently. It does not count if only gestured at vaguely.
- Judge FORM against what the audience asked for, not against a house style.
  Ask: is every heading, section label, table and bullet list carrying content
  that would be lost as plain sentences?
  - "fits" — the shape matches the request. A structured document that was
    ASKED for is "fits". So is plain prose answering a plain question. Terse is
    not a form defect.
  - "some_scaffolding" — mostly right, but one or two headings, meta-labels or
    a table exist to look organized rather than to carry content.
  - "report_theater" — a short answer wearing the costume of a long document:
    section headers over one or two sentences each, confidence tables, restated
    titles, process narration about how the answer was produced, or named
    frameworks the reader never asked for. The reader has to disassemble a
    deliverable to find an answer that fits in a paragraph.
- Process narration counts against form. The reader asked for an answer, not a
  description of the procedure that produced it.
- Do NOT penalize structure that is load-carrying: numbered steps in
  instructions, real tabular data, or a format the prompt explicitly requested.
- A response containing NO headings, no section labels and no tables cannot be
  "report_theater". If there is no scaffolding to quote, the form "fits".
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
    form = LABELS_FORM.get(parsed.get("form"), 10)
    if form < 10 and not (parsed.get("form_quote") or "").strip():
        form = 10     # could not point at the scaffolding it objected to
    return {"rule1_understandable": float(clarity), "rule4_imagery": float(imagery),
            "rule7_form": float(form)}
