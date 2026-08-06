"""Regression tests for rule 3 (jargon) and judge evidence standards."""
import unittest

from readability_eval.clarity import rule3_jargon
from readability_eval.judge import _is_sentence


def flagged(text, **kw):
    s, d = rule3_jargon(text, **kw)
    return d["undefined_acronyms"] + d["undefined_terms"]


class TestJargonTerms(unittest.TestCase):
    """The rule is named 'avoids jargon and acronyms' but only ever detected
    acronyms, so every undefined domain term scored a clean 10."""

    def test_domain_terms_are_caught(self):
        for t in ("The idempotent handler debounces the mutation.",
                  "Backfill the denormalized shard before cutover.",
                  "This introduces tail latency under contention.",
                  "Reduce overfitting with regularization."):
            self.assertTrue(flagged(t), t)

    def test_plain_prose_is_clean(self):
        for t in ("Set the modulator frequency to 30 Hz.",
                  "The cache expires after an hour.",
                  "The deploy failed because the disk was full."):
            self.assertEqual(flagged(t), [], t)


class TestJargonExemptions(unittest.TestCase):
    """Precision is not the defect. A term that is explained, assumed, or
    native to the reader costs nothing."""

    def test_inline_definition_exempts(self):
        self.assertEqual(
            flagged("The handler is idempotent, which means running it "
                    "twice is safe."), [])

    def test_parenthetical_exempts(self):
        self.assertEqual(
            flagged("We use sharding (splitting one database into several)."), [])

    def test_assumed_term_exempts(self):
        self.assertEqual(flagged("The handler is idempotent.",
                                 assumed=("idempotent",)), [])

    def test_expert_audience_exempts(self):
        """'throughput' is the right word for a sysadmin and noise in a lesson
        plan. Without this the rule flagged 22 correct uses in answers written
        FOR a sysadmin."""
        t = "Expect 3 Gbps of throughput per core."
        self.assertTrue(flagged(t, audience="hobbyist"))
        self.assertEqual(flagged(t, audience="sysadmin sizing a VPN server"), [])


class TestQuoteEvidence(unittest.TestCase):
    """A penalty must rest on a real quote. A judge pressed to name the worst
    sentence will otherwise point at markdown."""

    def test_markup_is_not_evidence(self):
        self.assertFalse(_is_sentence("*(\n---"))
        self.assertFalse(_is_sentence("###"))
        self.assertFalse(_is_sentence(""))

    def test_real_sentence_is_evidence(self):
        self.assertTrue(_is_sentence("The referent of this pronoun is unclear."))

    def test_headings_pass_the_lower_bar(self):
        """Form quotes name headings, which are legitimately short."""
        self.assertFalse(_is_sentence("Summary", min_words=2))
        self.assertTrue(_is_sentence("Overall Assessment", min_words=2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
