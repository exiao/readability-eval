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

# Paper uses CC > 10 with Radon's bounds. The prose equivalent of "this
# function has too many decision points" is a sentence the reader has to
# hold open: 4+ clauses. Measured on the control corpus, 4 sits at roughly
# the same tail position that CC>10 does for Python.
COMPLEX_CLAUSES = 4

_CLAUSE = re.compile(
    r",|\band\b|\bbut\b|\bor\b|\bwhich\b|\bthat\b|\bwhile\b|\bbecause\b"
    r"|\bwhen\b|\bif\b|\balthough\b|\bwhereas\b|\bso that\b|;|—| -- ", re.I)

_SENT = re.compile(r"[^.!?\n]+[.!?]?")


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
    """Decision points. 1 clause minimum, one per clause marker after that."""
    return 1 + len(_CLAUSE.findall(sent))


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
    bad = set(clone_sentences(text))
    for s in sents:
        hits, _ = lexicon.score(s)
        if hits > 0:
            bad.add(s)
    return round(len(bad) / len(sents), 3)


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
