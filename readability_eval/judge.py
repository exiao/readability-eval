"""Judge for rules 1 (understand), 4 (imagery) and 7 (form), plus fact delivery.

The judge emits ordered LABELS, never numbers, and must quote the offending
sentence. No quote means no penalty — this stops the judge inventing vague
complaints, which is the main failure mode of LLM-as-judge setups.

Coverage is judged too, because rule 2 needs a denominator: an answer must not
win on brevity by ignoring half the request. The judge marks which parts of the
ask were addressed, NOT whether the answer is factually right. This is a
readability benchmark; correctness is out of scope and would need ground truth
the real user prompts do not come with.
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

# Rules 2, 3, 5 and 6 are counted mechanically AND judged, then the worse of
# the two is taken (same belt-and-braces as rule 7). The counters are precise
# but blind: they only see the phrases on their lists, and 43 of 49 jargon
# terms plus 18 of 21 filler patterns never fire on real answers. A judge
# reading for the same defect catches the wording nobody thought to list.
# The counter still guards the other direction, since a judge waves through
# padding it finds pleasant.
LABELS_ECONOMY = {"tight": 10, "some_padding": 5, "bloated": 0}
LABELS_JARGON = {"plain": 10, "some_jargon": 5, "impenetrable": 0}
LABELS_SIMPLE = {"simple": 10, "some_complex": 5, "needlessly_complex": 0}
LABELS_FILLER = {"no_filler": 10, "some_filler": 5, "padded": 0}

TEMPLATE = """You are grading ONE response for readability. Be strict and literal.

AUDIENCE: {audience}

THE PROMPT THEY ANSWERED:
{prompt}

WHAT THE USER WANTED ADDRESSED (did the response address each one?):
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
  "facts_delivered": [true/false for each item above, in order],
  "clarity": "clear" | "needs_a_reread" | "opaque",
  "clarity_quote": "the exact sentence that is hardest to understand, or empty string if none",
  "imagery": "concrete" | "abstract_but_fine" | "needed_an_image",
  "imagery_quote": "the exact abstract sentence that needed a concrete image, or empty string if none",
  "imagery_suggestion": "the concrete image or example you would have used, or empty string",
  "form": "fits" | "some_scaffolding" | "report_theater",
  "form_quote": "the exact heading, label or table row that is doing no work, or empty string if none",
  "economy": "tight" | "some_padding" | "bloated",
  "economy_quote": "the exact sentence you would cut with no loss, or empty string if none",
  "jargon": "plain" | "some_jargon" | "impenetrable",
  "jargon_quote": "the exact undefined term, acronym or figure of speech this reader would stumble on, or empty string if none",
  "simple_words": "simple" | "some_complex" | "needlessly_complex",
  "simple_words_quote": "the exact complex word or phrase used where a simple one would do, or empty string if none",
  "filler": "no_filler" | "some_filler" | "padded",
  "filler_quote": "the exact filler, pretentious phrase or euphemism, or empty string if none"
}}

Rules for grading:
- Judge clarity FOR THE STATED AUDIENCE. A precise technical term a backend
  engineer knows is not a clarity problem. Replacing it with vague everyday
  words would be worse.
- "clear" means a competent member of that audience gets it on one read,
  START TO FINISH. Do not award it for an answer that is mostly readable with
  one sentence you had to parse twice: that is exactly "needs_a_reread", and
  it is the most common real verdict. Reserve "clear" for answers where you
  can honestly point at no sentence that slowed you down.
- Sentences that earn "needs_a_reread": a pronoun whose referent you had to
  hunt for, a clause stacked three deep, a sentence over about 40 words with
  no punctuation to break it, a term used before it is introduced, or a
  negation you had to read twice to resolve. Quote the worst one.
- When the audience is a machine or a script and the prompt asked for a data
  format (JSON, CSV, a single value), a bare well-formed payload is "clear" and
  its form "fits". Do not mark it opaque for lacking sentences, and do not
  demand explanation the prompt forbade.
- Only say "needed_an_image" if the text explains a relationship, process, or
  comparison in pure abstraction AND you can name the concrete image that fixes
  it. If you cannot name one, answer "abstract_but_fine".
- An item counts as addressed if the response engages with it substantively,
  even if worded differently. It does not count if only gestured at vaguely.
  Do NOT check whether the answer is factually CORRECT — this benchmark scores
  readability, not truth. A confidently wrong but clear answer still counts the
  item as addressed.
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
- THUMB TEST for sentences, not just headings. Cover any sentence. If the rest
  of the answer still delivers the same fact, number, instruction and stake,
  that sentence was never doing work. Two cases to look for:
    - a second sentence that only renames what the first already said, adding
      no constraint, number, consequence or next action
    - a sentence that only announces content that follows ("Here is the
      answer", "Three questions, in order") where numbered items and headings
      already announce their own structure
  A sentence that fails the thumb test is scaffolding even with no heading
  attached, and it is quotable in form_quote.
- ECONOMY: can words come out and the answer still be clear? Judge against
  what the QUESTION deserves, not against short-is-better. A long answer to a
  genuinely long question is "tight". Quote a sentence you would cut with no
  loss of fact, number, instruction or stake.
  - "tight" — nothing to cut without losing content.
  - "some_padding" — you can name a sentence or section that could go.
  - "bloated" — you could cut a third and lose nothing.
  Terse is never a defect here. An answer that skips half the request is
  already punished through coverage; do not punish it twice for being short.
- JARGON: would THIS audience stumble? Include undefined acronyms (BATNA,
  ZOPA, EMI) and figures of speech that assume shared context ("boil the
  ocean", "move the needle"). A precise term the stated reader knows is not
  jargon, and a term explained on the spot is not jargon. Quote the exact
  term, not the sentence around it.
- SIMPLE WORDS: a complex word where a simple one carries the same meaning
  ("utilize" for "use", "commence" for "start", "in order to" for "to").
  Do NOT flag a precise word that has no short synonym: "chrysalis" is not a
  complex word for "cocoon", it is a different thing. Quote the word.
- FILLER: words occupying space without carrying meaning. Four kinds, all
  count: empty intros ("it is worth noting that"), pretentious diction
  ("leverage", "seamless"), meaningless connective padding, and euphemism
  ("rightsizing" for layoffs). Euphemism is the worst of the four because the
  defect is dishonesty, not wordiness. Quote the exact phrase.
- For all four of the above: if you cannot quote it, the answer is the clean
  label. An unquotable complaint is not evidence.
- AND THE DEFAULT FOR ALL FOUR IS THE CLEAN LABEL. You are looking for real
  defects, not filling in a form. Most good answers are genuinely "tight",
  "plain", "simple" and "no_filler" on all four at once, and marking one down
  to look thorough is the failure mode here. Two specific traps:
  - A common short word is not jargon because it is informal. "infra", "app",
    "repo" read fine to the audience that uses them. Flag a term only if this
    reader would have to look it up.
  - A vivid sentence that carries an argument is not filler. "Neither promise
    survives contact with a deadline" states the reason for the decision.
    Filler is a phrase you can delete with NO loss of meaning, not a phrase
    you personally would have worded plainly.
- Do NOT penalize structure that is load-carrying: numbered steps in
  instructions, real tabular data, or a format the prompt explicitly requested.
- A response containing NO headings, no section labels and no tables can still
  be "some_scaffolding" if it fails the thumb test above, but reserve
  "report_theater" for answers whose STRUCTURE is the costume. If you cannot
  quote either a heading or a specific do-nothing sentence, the form "fits".
"""


def build_prompt(item, response):
    facts = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(item["asks"]))
    return TEMPLATE.format(audience=item["audience"], prompt=item["prompt"],
                           facts=facts, response=response)


def parse(raw):
    """Tolerant JSON extraction — judges wrap output in fences despite instructions."""
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"no JSON in judge output: {raw[:200]}")
    blob = m.group(0)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        # A judge that emits the object then keeps talking ("...}\n\nNote: I
        # scored form as...") produces trailing data the greedy match swallows.
        # Walk braces to find the first balanced object instead of failing the
        # whole run on one chatty response.
        depth = 0
        for i, ch in enumerate(blob):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(blob[:i + 1])
        raise


def _is_sentence(quote, min_words=4):
    """A quote counts as evidence only if it is prose.

    Judges under instruction to name the worst sentence will sometimes quote a
    fragment of markdown instead. Requiring a few real words keeps a penalty
    from resting on punctuation.
    """
    q = (quote or "").strip()
    if not q:
        return False
    words = re.findall(r"[A-Za-z']{2,}", q)
    return len(words) >= min_words


def merge_judged(det, jud):
    """Fold judged opinions on the counted rules into the counter scores.

    Takes the worse of the two. The counters only see the phrases on their
    lists; the judge reads for the same defect in wording nobody enumerated.
    Mutates and returns `det`, and returns `jud` stripped of judged_* keys so
    callers can splat both without leaking scratch keys into the rule set.
    """
    judged = {k[len("judged_"):]: v for k, v in jud.items()
              if k.startswith("judged_")}
    clean = {k: v for k, v in jud.items() if not k.startswith("judged_")}
    for rule, jscore in judged.items():
        if rule in det:
            det[rule] = min(det[rule], jscore)
    return det, clean


def to_scores(parsed):
    """Labels -> numbers. Quote required, else the penalty is dropped."""
    clarity = LABELS_CLARITY.get(parsed.get("clarity"), 5)
    if clarity < 10 and not _is_sentence(parsed.get("clarity_quote")):
        # Unsubstantiated complaint. The quote must be an actual sentence:
        # a judge pressed to find something hard to read will otherwise point
        # at markup ("*(\n---") and the penalty stands on nothing.
        clarity = 10
    imagery = LABELS_IMAGERY.get(parsed.get("imagery"), 7)
    if imagery < 7 and not (parsed.get("imagery_suggestion") or "").strip():
        imagery = 7   # could not name the image it wanted
    form = LABELS_FORM.get(parsed.get("form"), 10)
    if form < 10 and not _is_sentence(parsed.get("form_quote"), min_words=2):
        # Same evidence standard, lower bar: a heading is legitimately short
        # ("## Summary"), so two words is enough to name one.
        form = 10
    out = {"rule1_understandable": float(clarity),
           "rule4_imagery": float(imagery),
           "rule7_form": float(form)}
    # Judged opinions on the four counted rules. Returned under judged_* so the
    # caller can combine them with the counters rather than overwrite them.
    for rule, field, labels, floor in (
            ("rule2_economy", "economy", LABELS_ECONOMY, 4),
            ("rule3_jargon", "jargon", LABELS_JARGON, 1),
            ("rule5_simple_words", "simple_words", LABELS_SIMPLE, 1),
            ("rule6_filler", "filler", LABELS_FILLER, 1)):
        quote_key = field + "_quote"
        key = rule
        score = labels.get(parsed.get(field))
        if score is None:
            continue          # judge omitted it: fall back to the counter alone
        if score < 10 and not _is_sentence(parsed.get(quote_key),
                                           min_words=floor):
            score = 10        # unquotable complaint is not evidence
        out["judged_" + key] = float(score)
    return out
