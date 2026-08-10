"""Coverage cannot exceed 1.0, however many entries the judge returns.

`facts` comes from counting truthy items in a list the judge emits. Nothing
makes the judge return exactly one entry per ask, so an over-long list used to
multiply economy past 10 and carry the final score past 100.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readability_eval.clarity import score_all


def economy(text, delivered, required, budget):
    det, detail = score_all(text, delivered, (), required=required,
                            budget=budget, audience="general")
    return det["rule2_economy"], detail["economy"]


def test_extra_truthy_entries_cannot_push_coverage_above_one():
    # One ask, judge returned three truthy entries.
    score, detail = economy("A short answer." * 5, delivered=3, required=1,
                            budget=200)
    assert detail["coverage"] == 1.0
    assert score <= 10.0


def test_score_stays_within_range_on_over_coverage():
    from readability_eval.run import clarity_score
    rules = {"rule1_understandable": 10.0, "rule4_imagery": 10.0,
             "rule7_form": 10.0, "rule3_jargon": 10.0,
             "rule5_simple_words": 10.0, "rule6_filler": 10.0}
    score, detail = economy("Tight.", delivered=2, required=1, budget=200)
    rules["rule2_economy"] = score
    final = clarity_score(rules, detail["economy"].get("coverage")
                          if "economy" in detail else detail["coverage"]) * 10
    assert final <= 100.0


def test_full_coverage_still_scores_full():
    score, detail = economy("Answer.", delivered=2, required=2, budget=200)
    assert detail["coverage"] == 1.0
    assert score == 10.0


def test_partial_coverage_still_penalised():
    score, detail = economy("Answer.", delivered=1, required=4, budget=200)
    assert detail["coverage"] == 0.25
    assert score < 5.0
