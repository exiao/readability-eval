"""Deterministic clarity counters — rules 2, 3, 5, 6.

Rules 1 (easy to understand) and 4 (imagery) need a judge; see judge.py.
Each returns 0-10, higher is better.
"""
import re

# Rule 5: long form -> short form. Purely mechanical, cheapest signal here.
COMPLEX_PHRASES = {
    "utilize": "use", "utilizes": "uses", "utilizing": "using",
    "in order to": "to", "at this point in time": "now",
    "due to the fact that": "because", "owing to the fact that": "because",
    "has the ability to": "can", "have the ability to": "can",
    "is able to": "can", "are able to": "can",
    "in the event that": "if", "prior to": "before", "subsequent to": "after",
    "a large number of": "many", "a majority of": "most",
    "in close proximity to": "near", "make a decision": "decide",
    "provide assistance": "help", "on a regular basis": "regularly",
    "with regard to": "about", "in regard to": "about",
    "in the majority of cases": "usually", "for the purpose of": "to",
    "in spite of the fact that": "although", "at the present time": "now",
    "in a timely manner": "promptly", "take into consideration": "consider",
    "come to the conclusion": "conclude", "conduct an investigation": "investigate",
    "give consideration to": "consider", "is of the opinion": "thinks",
    "in the near future": "soon", "a sufficient number of": "enough",
    "despite the fact that": "although", "with the exception of": "except",
    "in conjunction with": "with", "subsequent upon": "after",
    "endeavor": "try", "commence": "start", "terminate": "end",
    "facilitate": "help", "ascertain": "find out", "necessitate": "require",
    "demonstrate": "show", "sufficient": "enough", "additional": "more",
    "approximately": "about", "component": "part", "initiate": "start",
    "methodology": "method", "numerous": "many", "obtain": "get",
    "purchase": "buy", "regarding": "about", "request": "ask",
    "require": "need", "reside": "live", "transmit": "send",
}

# Rule 6: three separate counters. Euphemism weighted highest — it is the only
# one where the defect is dishonesty rather than style.
FILLER = ["it is important to note", "it's important to note", "worth noting",
          "needless to say", "as we all know", "in today's world",
          "when it comes to", "the fact of the matter is", "it should be noted",
          "as previously mentioned", "in terms of", "the reality is"]
PRETENTIOUS = ["leverage", "leveraging", "operationalize", "ideate", "synergize",
               "paradigm", "holistic", "robust", "seamless", "delve", "utilize",
               "empower", "streamline", "foster", "underscore", "myriad",
               "plethora", "utilization", "optimize", "actionable"]
EUPHEMISM = ["rightsizing", "right-sizing", "headwinds", "challenging quarter",
             "learnings", "opportunity for improvement", "suboptimal",
             "not without its challenges", "restructuring", "synergies",
             "streamlining operations", "transition period", "let go"]

ACRONYM = re.compile(r"\b[A-Z]{2,6}s?\b")
COMMON_ACRONYMS = {"AI", "API", "URL", "HTTP", "HTTPS", "JSON", "CSV", "PDF",
                   "USA", "UK", "EU", "CEO", "CTO", "FAQ", "OK", "TV", "PC",
                   "ID", "IT", "PR", "QA", "UI", "UX", "SQL", "HTML", "CSS"}


def _hits(text, terms):
    low = text.lower()
    return sum(len(re.findall(r"\b" + re.escape(t) + r"\b", low)) for t in terms)


def _per100(n, words):
    return n / max(1, words) * 100


def _to10(rate, ceiling):
    """rate 0 -> 10, rate >= ceiling -> 0."""
    return round(max(0.0, 10.0 * (1 - min(1.0, rate / ceiling))), 1)


def rule2_economy(text, facts, required=None):
    """Words per fact delivered, gated by coverage. NOT raw brevity.

    Tested: a plain 70-word answer beat a jargon-heavy 95-word answer on all six
    rules while being useless. Scored on length alone, the emptiest text wins.

    First run of this eval exposed the weaker version of the same bug: a model
    answered in 44 words, delivered 2 of 4 required facts, and took the top
    economy score for it. Words-per-fact alone still rewards omission, because
    dropping a fact removes more words than it removes credit.

    Fix: multiply by coverage. Answering half the question caps economy at half,
    no matter how tersely you did it.
    """
    words = len(text.split())
    if facts <= 0:
        return 0.0, {"words": words, "facts": 0, "note": "no facts delivered"}
    wpf = words / facts
    # 15 w/fact is tight, 80 is padded.
    base = max(0.0, min(10.0, 10 * (1 - (wpf - 15) / 65)))
    coverage = 1.0 if not required else facts / required
    s = round(base * coverage, 1)
    return s, {"words": words, "facts": facts, "required": required,
               "coverage": round(coverage, 2), "words_per_fact": round(wpf, 1)}


def rule3_jargon(text, assumed=()):
    """Undefined terms + unexpanded acronyms per 100 words.

    Audience-relative: a term the reader is assumed to know costs nothing, and a
    term defined inline costs nothing. Precision is not a defect.
    """
    words = len(text.split())
    assumed = {a.upper() for a in assumed} | COMMON_ACRONYMS
    found = [a for a in ACRONYM.findall(text) if a.rstrip("s") not in assumed]
    undefined = []
    for a in set(found):
        # defined if followed/preceded by an expansion in parens
        if re.search(re.escape(a) + r"\s*\([^)]{4,}\)", text) or \
           re.search(r"\([^)]*" + re.escape(a) + r"[^)]*\)", text):
            continue
        undefined.append(a)
    rate = _per100(len(undefined), words)
    return _to10(rate, 6.0), {"undefined_acronyms": sorted(undefined),
                              "per_100w": round(rate, 2)}


def rule5_simple_words(text):
    words = len(text.split())
    low = text.lower()
    found = {}
    for long, short in COMPLEX_PHRASES.items():
        n = len(re.findall(r"\b" + re.escape(long) + r"\b", low))
        if n:
            found[long] = (n, short)
    rate = _per100(sum(v[0] for v in found.values()), words)
    return _to10(rate, 5.0), {"swaps": {k: v[1] for k, v in found.items()},
                              "per_100w": round(rate, 2)}


def rule6_filler(text):
    words = len(text.split())
    f, p, e = _hits(text, FILLER), _hits(text, PRETENTIOUS), _hits(text, EUPHEMISM)
    # euphemism x3: the defect is dishonesty, not style
    weighted = f + p + (e * 3)
    rate = _per100(weighted, words)
    return _to10(rate, 6.0), {"filler": f, "pretentious": p, "euphemism": e,
                              "per_100w": round(rate, 2)}


def score_all(text, facts, assumed=(), required=None):
    r2, d2 = rule2_economy(text, facts, required)
    r3, d3 = rule3_jargon(text, assumed)
    r5, d5 = rule5_simple_words(text)
    r6, d6 = rule6_filler(text)
    return {"rule2_economy": r2, "rule3_jargon": r3,
            "rule5_simple_words": r5, "rule6_filler": r6}, \
           {"economy": d2, "jargon": d3, "simple_words": d5, "filler": d6}
