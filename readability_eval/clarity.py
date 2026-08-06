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


# Filler is mostly a GRAMMAR shape, not a vocabulary. The fixed list below
# catches one exact wording each, so "worth noting" scores and "it is worth
# mentioning" walks past. Tested against 16 textbook filler constructions, the
# phrase list caught 1. These patterns cover the shapes that list cannot:
# expletive subjects, nominalised verbs, and stacked hedges.
FILLER_PATTERNS = [
    # "there is a X that ..." -- an expletive subject delaying the real one
    r"\bthere (?:is|are|was|were)\s+(?:a|an|the|no|some|several|many)?\s*"
    r"\w*\s*(?:that|which|who)\b",
    # "it is worth mentioning / important to remember"
    r"\bit(?:'s| is| was) (?:worth|important|useful|helpful|essential|critical|"
    r"interesting|necessary)\s+(?:to\s+)?\w+(?:ing|e|t|r)?\b",
    # wordy connectives with a one-word equivalent
    r"\bin order to\b",
    r"\bdue to the fact that\b",
    r"\bfor the (?:purpose|reason) of\b",
    r"\bin the event that\b",
    r"\bwith regard to\b",
    r"\bin spite of the fact that\b",
    # "the reason why X is because" -- says the same thing twice
    r"\bthe (?:reason|fact) (?:why|that)\b[^.]{0,40}\bis (?:because|that)\b",
    # time padding
    r"\bat (?:this|that) (?:point in time|moment in time)\b",
    r"\bin (?:today's|the modern) (?:world|landscape|era)\b",
    # restating instead of stating
    r"\bwhat (?:this|that) means is\b",
    r"\bthe (?:thing|point) (?:is|here) is that\b",
    # ceremonial openers
    r"\b(?:it goes without saying|first and foremost|last but not least)\b",
    r"\blet me (?:start|begin) by\b",
    r"\b(?:great|excellent|good) question\b",
    # stacked hedging: two or more qualifiers doing one qualifier's work
    r"\b(?:i think|i believe|it seems)\b[^.]{0,25}\b(?:probably|maybe|perhaps|"
    r"might|could possibly)\b",
    r"\b(?:may|might|can) (?:potentially|possibly)\b",
    r"\b(?:generally|typically|usually) (?:speaking|tends? to)\b",
    # "one of the most important things" -- ranking with no rank
    r"\bone of the (?:most|biggest|best|key) \w+ (?:things?|factors?|aspects?|"
    r"reasons?|ways?)\b",
    # filler adverbs opening a sentence
    r"(?:^|\. )(?:Basically|Essentially|Simply put|In essence|Needless to say)"
    r"\b",
]
_FILLER_RX = [re.compile(p, re.I) for p in FILLER_PATTERNS]


def _pattern_hits(text):
    text = lexicon.strip_quoted(text)
    return sum(len(rx.findall(text)) for rx in _FILLER_RX)


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
        # Coverage must still be reported. The early return used to omit it,
        # so a total non-answer looked like "coverage unknown" to the caller
        # and skipped the empty-answer cap entirely -- the exact case this
        # branch exists to catch.
        return 0.0, {"words": words, "facts": 0, "required": required,
                     "coverage": 0.0, "note": "no facts delivered"}
    budget = budget or 150
    # Decay is geometric rather than linear-to-zero. The old curve hit exactly
    # 0.0 at 3x budget and stayed there, which made every word past that point
    # free and let a 5000-word answer tie a 1050-word one. It also meant an
    # answer could gain ~31 points by being cut in half, purely by climbing off
    # the floor. Halving every 1.5x over budget keeps the penalty real without
    # ever bottoming out: 2x -> 6.3, 3x -> 4.0, 5x -> 1.6.
    over = max(0.0, (words - budget) / float(budget))
    base = 10.0 * (0.5 ** (over / 1.5))
    coverage = 1.0 if not required else facts / required
    s = round(base * coverage, 1)
    return s, {"words": words, "budget": budget, "facts": facts,
               "required": required, "coverage": round(coverage, 2),
               "over_budget": round(words / budget, 2)}


# Domain terms a general reader cannot decode from context. Kept deliberately
# short and specific: the rule is audience-relative, so a term the prompt marks
# as assumed costs nothing, and anything defined inline costs nothing. These
# are words that carry a precise meaning inside one field and none outside it.
JARGON_TERMS = {
    # distributed systems / backend
    "idempotent", "idempotency", "eventual consistency", "backpressure",
    "tail latency", "quorum", "sharding", "shard", "denormalized",
    "denormalization", "backfill", "cutover", "failover", "throughput",
    "contention", "reconciliation", "reconcile", "orchestration",
    "serialization", "deserialization", "middleware", "webhook",
    # data / ml
    "embedding", "vectorize", "inference", "fine-tune", "fine-tuning",
    "hyperparameter", "overfitting", "regularization", "gradient descent",
    "tokenization", "quantization", "ablation",
    # product / process
    "north star metric", "actionable insights", "value-add", "synergy",
    "bandwidth", "circle back", "double-click on", "socialize",
    "stakeholder alignment", "operationalize",
    # finance
    "amortization", "arbitrage", "basis points", "liquidity", "hedging",
}
_JARGON_RX = re.compile(
    r"\b(" + "|".join(sorted((re.escape(t) for t in JARGON_TERMS),
                             key=len, reverse=True)) + r")\b", re.I)


# Readers who own the vocabulary. A term is only jargon relative to someone:
# "throughput" is the correct word for a sysadmin sizing a VPN and pretentious
# noise in a lesson plan. Without this gate the rule flagged 22 uses of
# "throughput" in answers written FOR a sysadmin, which is not a defect, it is
# the right word for the reader.
EXPERT_AUDIENCE = re.compile(
    r"\b(?:engineer|developer|programmer|sysadmin|admin|devops|sre|architect|"
    r"data scientist|analyst|technical|scientist|researcher|trader|quant|"
    r"lawyer|clinician|physician|specialist|professional)\b", re.I)


def _undefined_jargon(text, assumed, audience=""):
    """Jargon terms that are neither assumed, explained, nor native to the reader.

    Three exemptions, because precision is not the defect:

    1. The prompt marks the term as assumed.
    2. The answer explains it on the spot. Generous on purpose: a
       parenthetical, a dash gloss, or "that is / which means" all count. A
       term named precisely and then unpacked is doing its job.
    3. The reader is an expert in the field the term belongs to. Only 8 of the
       30 prompts declare `assumed`, so the audience string has to carry this.
    """
    if EXPERT_AUDIENCE.search(audience or ""):
        return []
    scan = lexicon.strip_quoted(text)
    low_assumed = {a.lower() for a in assumed}
    out = []
    for m in _JARGON_RX.finditer(scan):
        term = m.group(1).lower()
        if term in low_assumed:
            continue
        after = scan[m.end():m.end() + 90]
        if re.match(r"\s*[(\u2014-]|\s*(?:,\s*)?(?:that is|which means|i\.e\.|"
                    r"meaning|or\b)", after, re.I):
            continue
        out.append(term)
    return out


def rule3_jargon(text, assumed=(), audience=""):
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
    terms = _undefined_jargon(text, assumed, audience)
    rate = _per100(len(undefined) + len(terms), words)
    return _to10(rate, 6.0), {"undefined_acronyms": sorted(undefined),
                              "undefined_terms": sorted(set(terms)),
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
    """Words that occupy space without carrying meaning.

    Three sources, weighted differently because they are different defects:
    a fixed phrase list, a set of grammatical patterns, and euphemism.

    The phrase list alone was close to useless. It matches one exact wording
    per entry, so "worth noting" scored and "it is worth mentioning" did not;
    against 16 textbook filler constructions it caught 1, and across 265 real
    responses it fired 3 times total. Filler is a shape ("there is X that...",
    "in order to", stacked hedges), not a vocabulary, so the patterns do the
    real work and the list is kept for the specific phrases it already knows.

    Euphemism still counts triple. The defect there is dishonesty rather than
    wordiness: "rightsizing" is not a long way to say "layoffs", it is a way
    to avoid saying it.
    """
    words = len(text.split())
    f, p, e = _hits(text, FILLER), _hits(text, PRETENTIOUS), _hits(text, EUPHEMISM)
    g = _pattern_hits(text)
    weighted = f + p + g + (e * 3)
    rate = _per100(weighted, words)
    return _to10(rate, 6.0), {"filler": f, "pretentious": p, "euphemism": e,
                              "grammar": g, "per_100w": round(rate, 2)}


def score_all(text, facts, assumed=(), required=None, budget=None, audience=""):
    r2, d2 = rule2_economy(text, facts, required, budget)
    r3, d3 = rule3_jargon(text, assumed, audience)
    r5, d5 = rule5_simple_words(text)
    r6, d6 = rule6_filler(text)
    return {"rule2_economy": r2, "rule3_jargon": r3,
            "rule5_simple_words": r5, "rule6_filler": r6}, \
           {"economy": d2, "jargon": d3, "simple_words": d5, "filler": d6}
