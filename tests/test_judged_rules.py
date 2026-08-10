"""Tests for the judged half of the counted rules (2, 3, 5, 6)."""
import unittest

from readability_eval.judge import merge_judged, to_scores


def parsed(**over):
    p = {"facts_delivered": [True], "clarity": "clear", "clarity_quote": "",
         "imagery": "concrete", "imagery_quote": "", "imagery_suggestion": "",
         "form": "fits", "form_quote": ""}
    p.update(over)
    return p


class TestJudgedRules(unittest.TestCase):
    def test_labels_map_to_scores(self):
        s = to_scores(parsed(jargon="some_jargon", jargon_quote="BATNA"))
        self.assertEqual(s["judged_rule3_jargon"], 5.0)

    def test_missing_field_is_omitted(self):
        """A judge that skips the field must fall back to the counter alone,
        not score zero."""
        self.assertNotIn("judged_rule3_jargon", to_scores(parsed()))

    def test_unquoted_complaint_is_dropped(self):
        """Same evidence standard as clarity and form: no quote, no penalty."""
        s = to_scores(parsed(filler="padded", filler_quote=""))
        self.assertEqual(s["judged_rule6_filler"], 10.0)

    def test_economy_needs_a_real_sentence(self):
        """Economy quotes a whole sentence, so the bar is 4 words."""
        s = to_scores(parsed(economy="bloated", economy_quote="---"))
        self.assertEqual(s["judged_rule2_economy"], 10.0)

    def test_jargon_quote_can_be_one_word(self):
        """Jargon quotes a term, not a sentence."""
        s = to_scores(parsed(jargon="some_jargon", jargon_quote="ZOPA"))
        self.assertEqual(s["judged_rule3_jargon"], 5.0)


class TestMergeJudged(unittest.TestCase):
    """Worse of counter and judge, the same belt-and-braces as rule 7."""

    def test_judge_can_lower_a_clean_counter(self):
        """The point of the change: counters miss what is not on their list."""
        det = {"rule3_jargon": 10.0}
        det, _ = merge_judged(det, {"judged_rule3_jargon": 5.0})
        self.assertEqual(det["rule3_jargon"], 5.0)

    def test_judge_cannot_raise_a_failing_counter(self):
        det = {"rule6_filler": 2.0}
        det, _ = merge_judged(det, {"judged_rule6_filler": 10.0})
        self.assertEqual(det["rule6_filler"], 2.0)

    def test_scratch_keys_do_not_leak(self):
        """judged_* must not end up in the rule set or it would be averaged
        into the score as an eighth rule."""
        _, clean = merge_judged({"rule3_jargon": 10.0},
                                {"rule1_understandable": 10.0,
                                 "judged_rule3_jargon": 5.0})
        self.assertEqual(clean, {"rule1_understandable": 10.0})

    def test_unknown_rule_is_ignored(self):
        det = {"rule3_jargon": 10.0}
        det, _ = merge_judged(det, {"judged_rule9_nonexistent": 0.0})
        self.assertEqual(det, {"rule3_jargon": 10.0})


if __name__ == "__main__":
    unittest.main(verbosity=2)
