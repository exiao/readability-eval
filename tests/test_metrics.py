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
