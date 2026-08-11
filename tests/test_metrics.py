"""Tests for the trajectory metrics ported from SlopCodeBench.

The contract that matters is ORDERING, not absolute values. Same reasoning as
the pairwise checks in data/controls.json: the level drifts with sentence
segmentation choices, but "tangled must beat clean" has to hold regardless.
"""
from readability_eval import metrics


CLEAN = (
    "Your migration moves to March 14. We found bad records in the old "
    "system. Fixing them takes two weeks. Your data stays where it is. "
    "Nothing is deleted. Call Sam with questions."
)

TANGLED = (
    "Your migration, which was originally scheduled for February 28 but has "
    "now been moved because we found inconsistencies in the legacy records "
    "that need resolving before we proceed, is going to happen on March 14, "
    "and while we understand this affects your planning, your data remains "
    "in place and nothing will be deleted, though you should contact Sam if "
    "you have questions about the revised timeline or the billing impact."
)


def test_erosion_is_bounded():
    for t in (CLEAN, TANGLED, "", "Hi."):
        assert 0.0 <= metrics.erosion(t) <= 1.0


def test_verbosity_is_bounded():
    for t in (CLEAN, TANGLED, "", "Hi."):
        assert 0.0 <= metrics.verbosity(t) <= 1.0


def test_tangled_erodes_more_than_clean():
    """The core ordering. Same facts, same length class, different shape."""
    assert metrics.erosion(TANGLED) > metrics.erosion(CLEAN)


def test_clean_short_sentences_erode_near_zero():
    assert metrics.erosion(CLEAN) < 0.15


def test_length_alone_is_not_erosion():
    """A long run of simple sentences must not read as eroded.

    Erosion is about complexity mass concentrating, not about size. If this
    fails the metric has collapsed into a word counter and duplicates what
    rule 2 already measures.
    """
    long_simple = " ".join(["The build failed." for _ in range(40)])
    assert metrics.erosion(long_simple) == 0.0


def test_repeated_sentence_counts_as_clone():
    text = ("The cache returns stale prices. " * 3) + "Set a shorter TTL."
    assert len(metrics.clone_sentences(text)) >= 2


def test_reworded_restatement_counts_as_clone():
    """Near-duplicates, not just exact repeats. Restating in fresh words is
    the prose form of copy-paste."""
    text = ("We found inconsistencies in the legacy records during checks. "
            "During checks we found inconsistencies in the legacy records. "
            "The new date is March 14.")
    assert len(metrics.clone_sentences(text)) >= 1


def test_distinct_sentences_are_not_clones():
    text = ("The migration slipped two weeks. Your data is untouched. "
            "Billing pauses until launch. Call Sam with questions.")
    assert metrics.clone_sentences(text) == []


def test_verbosity_counts_a_sentence_once():
    """The paper unions flagged and clone lines before dividing. A sentence
    that is both must not be double counted, which could push the ratio
    above 1.0."""
    text = ("Let's dive in and explore this. " * 4) + "Done."
    assert metrics.verbosity(text) <= 1.0


def test_headings_and_list_markers_are_stripped():
    text = "# Summary\n- first point here\n- second point here\n"
    sents = metrics.sentences(text)
    assert not any(s.startswith("#") or s.startswith("-") for s in sents)


def test_code_spans_do_not_count_as_prose():
    """Same mention-vs-use rule the lexicon already enforces. A doc showing
    a tangled snippet must not be scored as writing one."""
    plain = "Set the timeout. Restart the worker."
    withcode = plain + " Run `a, b, c and d or e, which if f, that g`."
    assert metrics.erosion(withcode) <= metrics.erosion(plain) + 0.01


def test_trend_positive_when_degrading():
    assert metrics.trend([0.1, 0.2, 0.3, 0.4]) > 0


def test_trend_negative_when_improving():
    assert metrics.trend([0.4, 0.3, 0.2]) < 0


def test_trend_needs_two_points():
    assert metrics.trend([0.5]) == 0.0
    assert metrics.trend([]) == 0.0


def test_trend_normalises_by_step_count():
    """Trajectories have different lengths, so drift is per CHECKPOINT, not
    total change. Otherwise an 8-checkpoint problem outweighs a 3-checkpoint
    one purely for being longer.

    Same total rise, more steps to get there, so the per-step rate is lower.
    """
    assert metrics.trend([0.0, 0.4]) > metrics.trend([0.0, 0.2, 0.4])
    assert metrics.trend([0.0, 0.2, 0.4]) == 0.2


def test_empty_text_does_not_crash():
    assert metrics.measure("") == {"erosion": 0.0, "verbosity": 0.0}


# --- Lists are not clauses -------------------------------------------------
# The first version counted commas and coordinators, so an enumeration read
# as deeply nested. On the saved corpus the eight highest-scoring sentences
# were all materials lists and label lines: every one a false positive, while
# the genuinely tangled sentences sat below them. These lock that shut.

MATERIALS = ("**Materials:** Shape cards or anchor chart (circle, triangle, "
             "square, rectangle, rhombus, trapezoid, pentagon, hexagon, "
             "octagon), whiteboards and markers, worksheet.")

CONTACT = ("If this revised timeline creates issues for your team, or if you "
           "have questions about the required action, your data, or billing, "
           "please contact [Name] at [Email] or [Phone].")

NESTED = ("If price updates go straight to the database — or arrive via a "
          "batch job that doesn't touch the cache — the old entry survives "
          "until TTL, which is why the divergence only shows up later.")


def test_label_line_is_one_clause():
    assert metrics.clauses(MATERIALS) == 1


def test_plain_list_is_one_clause():
    assert metrics.clauses("Buy eggs, milk, bread and butter.") == 1


def test_long_list_never_beats_real_nesting():
    """The ordering that was inverted. A 9-item materials list must not
    outrank a genuinely nested sentence."""
    assert metrics.clauses(MATERIALS) < metrics.clauses(NESTED)


def test_list_heavy_sentence_scores_modestly():
    """Eric flagged this one by eye: readable, mostly a list of nouns, and
    the metric had it at 10 clauses. It is not clean, but it must not be the
    worst sentence in the corpus."""
    assert metrics.clauses(CONTACT) <= 3


def test_coordinator_joining_clauses_still_counts():
    """The fix must not go so far that real coordination stops counting."""
    joined = "The build failed and we rolled back the release."
    listy = "The build uses cmake and ninja and clang."
    assert metrics.clauses(joined) > metrics.clauses(listy)


def test_verbless_fragment_is_one_clause():
    assert metrics.clauses("Data, access, cost, scope, backups.") == 1


def test_threshold_flags_the_tail_not_the_bulk():
    """A metric that fires on everything, or on nothing, is dead either way.
    Ordinary sentences must sit under the bar."""
    ordinary = ["We shipped the fix.",
                "Your migration moves to March 14.",
                "Call Sam with questions.",
                "Buy eggs, milk and bread."]
    assert all(metrics.clauses(s) <= metrics.COMPLEX_CLAUSES
               for s in ordinary)
    assert metrics.clauses(NESTED) > metrics.COMPLEX_CLAUSES



def test_verbosity_counts_every_duplicate_occurrence():
    """One sentence repeated 10 times is near-total repetition, not 10%.

    Keying the numerator on sentence TEXT collapsed all repeats into a single
    entry while the denominator kept all 10, scoring the worst possible input
    at 0.1.
    """
    sent = "The quick brown fox jumped over the lazy dog today."
    assert metrics.verbosity(" ".join([sent] * 10)) >= 0.8


def test_comma_joined_independent_clauses_are_not_a_list():
    """Three comma-separated INDEPENDENT clauses are load, not a scan.

    Forcing them to one clause hid their weight from the erosion headline.
    """
    assert not metrics._is_list_line(
        "We ship today, but they receive it tomorrow, so we must prepare.")
    assert metrics._is_list_line("Bring cards, markers, worksheets, and glue.")


def test_coordinator_with_noun_subject_still_counts():
    """Coordinated clauses may start with ordinary noun phrases, not only
    pronouns. They must not be mistaken for a comma-delimited list.
    """
    joined = ("The cache expired, but the database remained stale, so the "
              "service returned old prices.")
    assert not metrics._is_list_line(joined)
    assert metrics.clauses(joined) == 3
