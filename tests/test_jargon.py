"""Regression tests for rule 3 (jargon) and judge evidence standards.

FIXTURE POLICY: the positive cases below are VERBATIM sentences from
results/*.json, not sentences written to match the regex. An earlier version
of this file tested "the idempotent handler debounces the mutation before
reconciliation" -- a sentence invented to be caught, proving only that the
author could write to their own pattern. If you add a case, quote a real
answer and note where it came from.
"""
import unittest

from readability_eval.clarity import rule3_jargon
from readability_eval.judge import _is_sentence


def flagged(text, **kw):
    _, d = rule3_jargon(text, **kw)
    return d["undefined_acronyms"] + d["undefined_terms"]


class TestJargonTerms(unittest.TestCase):
    """The rule is named 'avoids jargon and acronyms' but only ever detected
    acronyms, so an undefined domain term scored a clean 10."""

    # verbatim, kimi-k3 prompt 5, audience "Concerned tech-savvy citizen"
    REAL_BANDWIDTH = ("Radio/TV transmitters, wartime-broadcaster style. "
                      "Low bandwidth, but physically hard to spoof at scale.")

    def test_real_undefined_term_is_caught(self):
        self.assertIn("bandwidth", flagged(self.REAL_BANDWIDTH,
                                           audience="concerned citizen"))

    def test_business_speak_is_caught(self):
        for t in ("Let me circle back on stakeholder alignment.",
                  "This is table stakes for the next quarter."):
            self.assertTrue(flagged(t, audience="parent"), t)

    def test_ordinary_long_words_are_not_jargon(self):
        """The corpus is teachers and negotiation curricula. 'communication'
        and 'chrysalis' are long, common, and not jargon."""
        for t in ("The caterpillar forms a chrysalis and waits.",
                  "Good communication resolves most negotiation conflicts.",
                  "Students will identify each stage of the lifecycle."):
            self.assertEqual(flagged(t, audience="teacher"), [], t)


class TestJargonExemptions(unittest.TestCase):
    """Precision is not the defect. A term that is explained, assumed, or
    native to the reader costs nothing."""

    def test_inline_definition_exempts(self):
        self.assertEqual(
            flagged("We watch throughput, which means how much data moves "
                    "per second.", audience="parent"), [])

    def test_parenthetical_exempts(self):
        self.assertEqual(
            flagged("Check the bandwidth (how much the line can carry).",
                    audience="parent"), [])

    def test_assumed_term_exempts(self):
        self.assertEqual(flagged("Throughput drops with small packets.",
                                 assumed=("throughput",),
                                 audience="parent"), [])

    def test_expert_audience_exempts(self):
        """Verbatim from claude-opus-4-6, prompt 10. The audience is a
        sysadmin sizing a VPN: 'throughput' is the correct word for that
        reader. Flagging it counted 22 correct usages as defects."""
        real = ("If the CPU supports AES-NI or has optimized ChaCha20 "
                "instructions, throughput increases significantly.")
        self.assertTrue(flagged(real, audience="hobbyist"))
        self.assertEqual(flagged(real, audience="sysadmin sizing a VPN server"),
                         [])


class TestQuoteEvidence(unittest.TestCase):
    """A penalty must rest on a real quote. Verbatim from a judge run: asked
    to name the hardest sentence, it answered '*(\\n---'."""

    def test_markup_is_not_evidence(self):
        self.assertFalse(_is_sentence("*(\n---"))
        self.assertFalse(_is_sentence("###"))
        self.assertFalse(_is_sentence(""))

    def test_real_sentence_is_evidence(self):
        self.assertTrue(_is_sentence(
            "Students build schemas for courses, instructors, and departments."))

    def test_headings_pass_the_lower_bar(self):
        """Form quotes name headings, which are legitimately short."""
        self.assertFalse(_is_sentence("Summary", min_words=2))
        self.assertTrue(_is_sentence("Overall Assessment", min_words=2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
