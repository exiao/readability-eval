"""Deterministic clarity counters — rules 2, 3, 5, 6.

Rules 1 (easy to understand) and 4 (imagery) need a judge; see judge.py.
Each returns 0-10, higher is better.
"""
import re

from . import lexicon

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

# Ordinary English words written in caps for emphasis are not acronyms. Backed by
# the system word list where available, with a small fallback for portability.
_WORDS_FILE = "/usr/share/dict/words"
try:
    with open(_WORDS_FILE) as _f:
        _ENGLISH = {w.strip().upper() for w in _f if 2 <= len(w.strip()) <= 6}
except OSError:  # pragma: no cover - platform dependent
    _ENGLISH = set()
_FALLBACK = {
    "THE", "AND", "NOT", "ALL", "BIG", "FUN", "NEW", "OLD", "YES", "NO", "IS",
    "IN", "ON", "AT", "TO", "OF", "IT", "BE", "DO", "GO", "SO", "UP", "WE",
    "YOU", "ONE", "TWO", "SIX", "TEN", "WHAT", "WHY", "HOW", "WHO", "NOW",
    "STOP", "GOOD", "BEST", "REAL", "SAME", "LIFE", "TIME", "WEEK", "YEAR",
    "SHAPE", "RULE", "GREAT", "EQUAL", "FLAT", "ROLL", "MEET", "HIDE", "SIDES",
    "THREE", "CIRCLE", "SQUARE", "OVAL", "SCENE", "SCRIPT", "SECRET", "VIDEO",
    "LESSON", "NOTE", "TIP", "STEP", "WARM", "COOL", "DOWN", "OVER", "END",
}


def _is_shouted_word(token):
    """True when an all-caps token is just an English word being emphasised."""
    base = token.rstrip("s").upper()
    return base in _ENGLISH or base in _FALLBACK or token.upper() in _FALLBACK
COMMON_ACRONYMS = {"AI", "API", "URL", "HTTP", "HTTPS", "JSON", "CSV", "PDF",
                   "USA", "UK", "EU", "CEO", "CTO", "FAQ", "OK", "TV", "PC",
                   "ID", "IT", "PR", "QA", "UI", "UX", "SQL", "HTML", "CSS"}


def _hits(text, terms):
    # Strip quoted/code spans first. Same mention-vs-use bug the slop lexicon
    # had: a text SAYING don't write "delve" was scored as writing it. Fixed in
    # lexicon.py but missed here, caught by the meta_slop_discussion control.
    text = lexicon.strip_quoted(text)
    low = text.lower()
    return sum(len(re.findall(r"\b" + re.escape(t) + r"\b", low)) for t in terms)


def _per100(n, words):
    return n / max(1, words) * 100


def _to10(rate, ceiling):
    """rate 0 -> 10, rate >= ceiling -> 0."""
    return round(max(0.0, 10.0 * (1 - min(1.0, rate / ceiling))), 1)


def rule2_economy(text, facts, required=None, budget=None):
    """Length against the budget the QUESTION deserves, gated by coverage.

    Not raw brevity: a plain 70-word answer beat a jargon-heavy 95-word answer
    on all six rules while being useless. Scored on length alone, the emptiest
    text wins.

    Not words-per-fact either. That was the previous version and it had no
    sense of what was asked, so it punished every genre whose deliverable is
    long. A complete 460-word postmortem hitting 4/4 facts scored 0.0, the same
    as a rambling non-answer, because the fact list only has 4 entries.

    Each prompt now declares a `budget`: the words a good answer to THAT
    question needs. "Why is the sky blue?" gets 100. A leaked-key runbook gets
    250. A bare JSON payload gets 20. Under budget is free — terse is never
    punished. Over budget decays, and 3x budget scores 0. This is what makes a
    long answer to a simple question score badly while a long answer to a
    genuinely long question does not.

    Coverage still multiplies: answering half the question caps economy at
    half, no matter how tersely you did it.
    """
    words = len(text.split())
    if facts <= 0:
        return 0.0, {"words": words, "facts": 0, "note": "no facts delivered"}
    budget = budget or 150
    overrun = max(0.0, (words - budget) / (2.0 * budget))  # 0 at budget, 1 at 3x
    base = max(0.0, 10.0 * (1 - min(1.0, overrun)))
    coverage = 1.0 if not required else facts / required
    s = round(base * coverage, 1)
    return s, {"words": words, "budget": budget, "facts": facts,
               "required": required, "coverage": round(coverage, 2),
               "over_budget": round(words / budget, 2)}


def rule3_jargon(text, assumed=()):
    """Undefined terms + unexpanded acronyms per 100 words.

    Audience-relative: a term the reader is assumed to know costs nothing, and a
    term defined inline costs nothing. Precision is not a defect.

    SHOUTING IS NOT AN ACRONYM. The regex matches any 2-6 letter run of capitals,
    which also catches emphasis and headings. A grade-2 lesson plan containing
    "SHAPE HUNT!" and "THE BIG RULE" scored 6.2 with 31 "undefined acronyms",
    every one of them an ordinary English word in caps. Any all-caps token that
    is a real lowercase English word is treated as emphasis, not jargon.
    """
    words = len(text.split())
    assumed = {a.upper() for a in assumed} | COMMON_ACRONYMS
    scan = lexicon.strip_quoted(text)
    found = [a for a in ACRONYM.findall(scan)
             if a.rstrip("s") not in assumed and not _is_shouted_word(a)]
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
    low = lexicon.strip_quoted(text).lower()
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


def score_all(text, facts, assumed=(), required=None, budget=None):
    r2, d2 = rule2_economy(text, facts, required, budget)
    r3, d3 = rule3_jargon(text, assumed)
    r5, d5 = rule5_simple_words(text)
    r6, d6 = rule6_filler(text)
    return {"rule2_economy": r2, "rule3_jargon": r3,
            "rule5_simple_words": r5, "rule6_filler": r6}, \
           {"economy": d2, "jargon": d3, "simple_words": d5, "filler": d6}
