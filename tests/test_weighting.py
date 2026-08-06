"""Regression tests for slop weighting and list/fragment discrimination."""
import unittest

from readability_eval.lexicon import (WEIGHTS, noun_list_fragments,
                                      rule_of_three, score)


class TestRuleOfThree(unittest.TestCase):
    def test_concrete_noun_list_is_not_padding(self):
        """The naive version fired on any three-item list and was this
        scorer's single largest error: 262 hits across 265 responses, costing
        some answers the entire 30% slop cap for writing a normal list."""
        self.assertEqual(rule_of_three("Rent, transportation, and food."), [])
        self.assertEqual(
            rule_of_three("Students learn circle, triangle, and rectangle."), [])

    def test_adjective_padding_in_prose_fires(self):
        t = "It is a thoughtful, ethical, and effective approach."
        self.assertEqual(len(rule_of_three(t)), 1)

    def test_heading_triple_is_a_label(self):
        """In a heading the triple IS the content, not padding."""
        self.assertEqual(
            rule_of_three("## Measurement, Reporting, and Accountability"), [])
        self.assertEqual(
            rule_of_three("- Measurement, Reporting, and Accountability"), [])


class TestNounListFragment(unittest.TestCase):
    def test_verbless_comma_list_fires(self):
        """No verb, no conjunction: a pile of nouns with the rhythm of a
        sentence and none of the content of one."""
        self.assertEqual(len(noun_list_fragments("Rent, transportation, food.")), 1)

    def test_anaphora_fragment_fires(self):
        t = "New quirks, new prompts, new failure modes."
        self.assertEqual(len(noun_list_fragments(t)), 1)

    def test_conjunction_makes_it_a_real_list(self):
        """The missing 'and' is the tell. Put it back and it is just a list."""
        self.assertEqual(noun_list_fragments("Rent, transportation, and food."), [])

    def test_verb_disqualifies(self):
        self.assertEqual(
            noun_list_fragments("It covers rent, transportation, food."), [])

    def test_bullets_and_headings_exempt(self):
        self.assertEqual(noun_list_fragments("- Rent, transportation, food"), [])
        self.assertEqual(noun_list_fragments("## Rent, transportation, food"), [])


class TestWeighting(unittest.TestCase):
    def test_unambiguous_outweighs_contextual(self):
        """A banned word should cost more than a formatting habit."""
        self.assertGreater(WEIGHTS["ai_vocab"], WEIGHTS["rule_of_three"])
        self.assertGreater(WEIGHTS["rule_of_three"], WEIGHTS["inline_header_list"])

    def test_labelled_bullets_do_not_dominate(self):
        """231 of 265 responses used labelled bullets. That formatting alone
        must not out-score real vocabulary offences."""
        bullets = "\n".join(f"- **Field {i}**: value" for i in range(10))
        vocab = "We delve into the robust seamless realm."
        self.assertGreater(score(vocab)[0], score(bullets)[0])

    def test_breakdown_reports_raw_counts(self):
        """Weights change the score, not the reported counts."""
        _, b = score("We delve into the delve of delve.")
        self.assertEqual(b["ai_vocab"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
