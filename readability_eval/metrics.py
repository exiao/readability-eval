"""Trajectory quality metrics, ported from SlopCodeBench (arXiv 2603.24755).

The paper's claim: single-shot benchmarks miss the failure that matters,
because quality degrades as an agent repeatedly extends its OWN prior output.
It tracks two signals per checkpoint, both bounded [0,1] so they are
comparable across runs and across trajectory lengths.

Their definitions are for code. The prose analogues here keep the same shape,
which is the part that carries the finding:

  erosion   = share of total complexity MASS held by units over a threshold
  verbosity = share of lines that are redundant or duplicated

Code               ->  Prose
callable           ->  sentence
cyclomatic compl.  ->  clause count (commas, conjunctions, subordinators)
SLOC               ->  words
clone lines        ->  near-duplicate sentences (shingle overlap)
AST-grep waste     ->  the existing lexicon's slop hits

Deliberately NOT a judge call. These are cheap deterministic counters, so a
trajectory costs the same as the answers it already generated.
"""
import re

from . import lexicon

# Paper uses CC > 10, following Radon's bounds, which puts roughly the top
# few percent of Python functions over the line. The prose threshold is set
# to sit in the same tail position, not to match the number.
#
# Recalibrated after the clause counter was fixed. Counting list commas
# inflated everything, so 4 was the tail then. Now that only real nesting
# counts, the distribution over 2540 measured sentences is 75% at 1 clause,
# 95% at 3, 99% at 4 -- so >2 marks the top ~6%, which is where CC>10 sits
# for code. Left at 4 it flagged 50 sentences in the whole corpus and the
# metric went dead.
COMPLEX_CLAUSES = 2


# A CLAUSE needs a verb. An enumeration does not.
#
# The first version of this counted commas and conjunctions, which made
# "your data, or billing, or [Phone]" read as three clauses. On the saved
# corpus the eight worst-scoring sentences were ALL materials lists and
# **Objective:** label lines -- "circle, triangle, square, rectangle,
# rhombus, trapezoid" scored 21. Every one was a false positive, and the
# real offenders were nowhere near the top.
#
# A list is flat: the reader holds one open slot and fills it repeatedly.
# A clause is nested: each one opens a new slot before the last one closed.
# That is the difference the metric has to see, and it is why erosion needs
# to key on subordination rather than punctuation.

# Subordinators and relatives open a dependent clause. These carry a verb
# by definition, so they are counted directly.
_SUBORD = re.compile(
    r"\b(which|who|whom|whose|that|because|although|though|while|whereas|"
    r"unless|until|since|whenever|wherever|if|when|after|before|"
    r"so that|even though|in order to|as long as|provided that|given that|"
    r"despite)\b", re.I)

# Coordinators only join clauses when what FOLLOWS has its own subject and
# verb. "eggs and milk" is a list; "it failed and we rolled back" is two
# clauses. There is no POS tagger here, so accept pronoun subjects and the
# common determiner + noun + finite-verb shape. Requiring a determiner keeps
# bare noun enumerations such as "cards and markers" out of the match.
_COORD_CLAUSE = re.compile(
    r"\b(?:and|but|or|yet|so)\s+"
    r"(?:"
    r"(?:i|we|you|he|she|it|they|this|that|these|those|there)\b\s+"
    r"(?:\w+)"
    r"|"
    r"(?:a|an|the|this|that|these|those)\s+"
    r"(?:\w+\s+){1,3}"
    r"(?:is|are|was|were|be|been|being|has|have|had|does|do|did|"
    r"will|would|can|could|should|may|might|must|\w+(?:ed|ing))\b"
    r"|"
    # Third-person present verbs after a simple determiner + noun subject:
    # "but the database remains stale". The verb must be followed by more
    # words, so a trailing noun phrase ("and the ripe bananas.") stays a list.
    r"(?:a|an|the|this|that|these|those)\s+\w+\s+\w+s\s+\w"
    r")", re.I)

# Semicolons and dashes joining two independent statements.
_HARD_BREAK = re.compile(r";|\s—\s|\s--\s")

# A finite verb somewhere, so fragments and label lines score as one unit
# rather than accumulating. "**Materials:** cards, markers, worksheet" has
# no verb at all and must not read as complex.
_VERBISH = re.compile(
    r"\b(is|are|was|were|be|been|being|has|have|had|do|does|did|will|would|"
    r"can|could|should|may|might|must|\w+s|\w+ed|\w+ing)\b", re.I)

_SENT = re.compile(r"[^.!?\n]+[.!?]?")


def _is_list_line(sent):
    """Label lines and enumerations, which are flat rather than nested.

    Three or more comma-separated fragments with no subordinator is a list,
    however long it gets. Reading it is a scan, not a stack.
    """
    if re.match(r"^\*{0,2}[A-Z][\w /-]{0,30}:\*{0,2}\s", sent):
        return True
    parts = [p for p in sent.split(",") if p.strip()]
    if len(parts) < 3 or _SUBORD.search(sent):
        return False
    # Comma-separated INDEPENDENT clauses are not a list: "We ship today, but
    # they receive it tomorrow, so we must prepare" is three clauses to hold,
    # not three items to scan. A coordinator followed by its own subject and
    # verb is the tell.
    if _COORD_CLAUSE.search(sent):
        return False
    return True



def sentences(text):
    """Prose sentences, minus headings, list markers and code."""
    text = lexicon.strip_quoted(text)
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("|"):
            continue
        s = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", s)
        for m in _SENT.finditer(s):
            frag = m.group(0).strip()
            if len(frag.split()) >= 3:
                out.append(frag)
    return out


def clauses(sent):
    """Nesting depth: how many things the reader holds open at once.

    Counts subordinate clauses, clause-joining coordinators and hard breaks.
    Does NOT count list commas, because a list is flat. A sentence with no
    verb at all is a label or fragment and scores 1 whatever its length.
    """
    if _is_list_line(sent) or not _VERBISH.search(sent):
        return 1
    return (1
            + len(_SUBORD.findall(sent))
            + len(_COORD_CLAUSE.findall(sent))
            + len(_HARD_BREAK.findall(sent)))



def mass(sent):
    """mass(f) = CC(f) * sqrt(SLOC(f)), verbatim from the paper (eq. 2).

    The square root compresses size so complexity dominates rather than
    pure length. A long simple sentence is not the defect; a long tangled
    one is.
    """
    return clauses(sent) * (len(sent.split()) ** 0.5)


def erosion(text):
    """Share of complexity mass sitting in over-complex sentences (eq. 3).

    Rises when a model answers a new requirement by bolting a clause onto a
    sentence that was already doing too much, instead of writing a new one.
    That is the prose form of the paper's central finding: agents patch
    existing functions rather than distributing logic.
    """
    sents = sentences(text)
    if not sents:
        return 0.0
    total = sum(mass(s) for s in sents)
    if total <= 0:
        return 0.0
    heavy = sum(mass(s) for s in sents if clauses(s) > COMPLEX_CLAUSES)
    return round(heavy / total, 3)


def _shingles(sent, n=4):
    w = re.findall(r"[a-z0-9]+", sent.lower())
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def clone_sentences(text, thresh=0.5):
    """Sentences that substantially repeat an earlier one.

    The paper counts clone LINES normalized by LOC. Restating a point in
    fresh words is the prose version of copy-paste: the reader pays for it
    twice and learns nothing the second time.
    """
    sents = sentences(text)
    seen, dupes = [], []
    for s in sents:
        sh = _shingles(s)
        if not sh:
            continue
        for prev in seen:
            if not prev:
                continue
            overlap = len(sh & prev) / min(len(sh), len(prev))
            if overlap >= thresh:
                dupes.append(s)
                break
        seen.append(sh)
    return dupes


def verbosity(text):
    """{flagged sentences U clone sentences} / sentences (eq. 4).

    Flagged = a sentence carrying a lexicon slop hit, standing in for the
    paper's 137 AST-grep waste rules. Union before counting, so a sentence
    that is both a clone and slop counts once, as the paper specifies.
    """
    sents = sentences(text)
    if not sents:
        return 0.0
    # Flag by POSITION, not by text. Keying on the sentence string collapsed
    # every repeat of a verbatim-duplicated sentence into one numerator entry
    # while all of its occurrences stayed in the denominator, so the worst
    # possible input (one sentence repeated N times) scored near 0.
    clones = clone_sentences(text)
    remaining = {}
    for s in clones:
        remaining[s] = remaining.get(s, 0) + 1
    bad = 0
    for s in sents:
        if remaining.get(s):
            remaining[s] -= 1
            bad += 1
            continue
        hits, _ = lexicon.score(s)
        if hits > 0:
            bad += 1
    return round(bad / len(sents), 3)


def measure(text):
    return {"erosion": erosion(text), "verbosity": verbosity(text)}


def trend(values):
    """Per-checkpoint drift. Positive = degrading.

    The paper's headline is not the level, it is the direction: erosion rose
    in 80% of trajectories, verbosity in 89.8%. A model can start clean and
    still be the worst one to iterate with.
    """
    if len(values) < 2:
        return 0.0
    return round((values[-1] - values[0]) / (len(values) - 1), 4)
