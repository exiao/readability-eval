"""Regression tests for economy weighting and the truncation exploit."""
import unittest

from readability_eval.clarity import rule2_economy
from readability_eval.run import RULE_WEIGHTS, clarity_score


def full(**over):
    r = {"rule1_understandable": 9.0, "rule2_economy": 9.0, "rule3_jargon": 9.0,
         "rule4_imagery": 9.0, "rule5_simple_words": 9.0, "rule6_filler": 9.0,
         "rule7_form": 9.0}
    r.update(over)
    return r


class TestTruncationExploit(unittest.TestCase):
    """Cutting an answer in half cannot make it a better answer. Any scorer
    that rewards truncation is measuring length, not quality."""

    def test_halving_a_long_answer_is_worth_little(self):
        long_e = rule2_economy("w " * 2000, 4, 4, 500)[0]
        half_e = rule2_economy("w " * 1000, 4, 4, 500)[0]
        gain = (clarity_score(full(rule2_economy=half_e), 1.0)
                - clarity_score(full(rule2_economy=long_e), 1.0)) * 10
        self.assertLess(gain, 5.0, "truncation must not be a scoring strategy")

    def test_economy_never_bottoms_out(self):
        """The old curve hit 0.0 at 3x budget and stayed there, so every word
        past that point was free and a 5000-word answer tied a 1050-word one."""
        e3 = rule2_economy("w " * 1500, 4, 4, 500)[0]
        e10 = rule2_economy("w " * 5000, 4, 4, 500)[0]
        self.assertGreater(e3, e10, "more bloat must always cost more")
        self.assertGreater(e10, 0.0)

    def test_over_budget_still_hurts(self):
        """Underweighting economy must not make verbosity free."""
        tight = clarity_score(full(rule2_economy=10.0), 1.0) * 10
        bloated = clarity_score(full(rule2_economy=2.0), 1.0) * 10
        self.assertGreater(tight - bloated, 5.0)


class TestEconomyWeight(unittest.TestCase):
    def test_economy_weighs_less_than_other_rules(self):
        self.assertLess(RULE_WEIGHTS["rule2_economy"], 1.0)

    def test_verbosity_is_not_a_non_answer(self):
        """Economy at 0 used to trip the conjunctive cap and score a merely
        long answer like one that said nothing: 15 of 19 caps in the corpus,
        about 31 points each."""
        self.assertGreater(clarity_score(full(rule2_economy=0.0), 1.0) * 10, 55.0)

    def test_unclear_answer_still_capped(self):
        self.assertLessEqual(
            clarity_score(full(rule1_understandable=0.0), 1.0) * 10, 55.0)


class TestEmptyAnswerGuard(unittest.TestCase):
    def test_no_coverage_caps_the_score(self):
        """The case economy used to guard: clean prose that answers nothing."""
        self.assertLessEqual(clarity_score(full(rule2_economy=0.0), 0.0) * 10,
                             55.0)

    def test_zero_facts_reports_coverage(self):
        """The early return omitted coverage, so a total non-answer looked
        like 'coverage unknown' and skipped the cap entirely."""
        _, d = rule2_economy("They differ. Use whichever fits.", 0, 3, 120)
        self.assertEqual(d["coverage"], 0.0)

    def test_partial_coverage_is_not_capped(self):
        self.assertGreater(clarity_score(full(), 0.67) * 10, 55.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
