"""Regression tests for rule 6 (filler)."""
import unittest

from readability_eval.clarity import rule6_filler


def hits(text):
    _, d = rule6_filler(text)
    return d["filler"] + d["pretentious"] + d["euphemism"] + d["grammar"]


class TestGrammarShapes(unittest.TestCase):
    """The fixed phrase list matched one exact wording per entry, so a
    paraphrase walked past it. Against these 16 constructions it caught 1."""

    def test_expletive_subject(self):
        self.assertTrue(hits("There are several factors that you should weigh."))

    def test_paraphrased_empty_intro(self):
        """'worth noting' was on the list; 'it is worth mentioning' was not."""
        self.assertTrue(hits("It is worth mentioning that the index is missing."))

    def test_wordy_connectives(self):
        for t in ("In order to run it, check the log.",
                  "Due to the fact that the disk is full, writes fail.",
                  "In the event that it fails, retry."):
            self.assertTrue(hits(t), t)

    def test_redundant_causation(self):
        self.assertTrue(hits("The reason why this happens is because the key is missing."))

    def test_stacked_hedges(self):
        for t in ("I think you should probably restart it.",
                  "This may potentially cause a timeout.",
                  "Generally speaking, Postgres handles this well."):
            self.assertTrue(hits(t), t)

    def test_ceremonial_openers(self):
        for t in ("First and foremost, check the logs.",
                  "Let me start by saying this is tricky.",
                  "Great question! Here is the answer."):
            self.assertTrue(hits(t), t)


class TestNoFalsePositives(unittest.TestCase):
    """Filler patterns are grammar shapes, so they are the easiest rule to
    over-fire. Plain technical prose must stay clean."""

    def test_plain_prose_is_clean(self):
        for t in ("The cache expires after an hour, which keeps memory flat.",
                  "Restart the service, then check the log for a bind error.",
                  "There is no index on user_id.",
                  "Ring modulation multiplies the voice with a carrier.",
                  "The deploy failed because the disk was full.",
                  "Set the modulator frequency between 30 and 300 Hz."):
            self.assertEqual(hits(t), 0, t)

    def test_bare_there_is_is_not_filler(self):
        """'There is no index' states a fact. Only the delaying form, where a
        relative clause carries the real subject, is filler."""
        self.assertEqual(hits("There is no index on that column."), 0)

    def test_mention_is_not_use(self):
        """Same bug the slop lexicon had: prose ABOUT filler is not filler."""
        self.assertEqual(hits('Avoid writing "in order to" when "to" will do.'), 0)


class TestScoring(unittest.TestCase):
    def test_euphemism_weighs_triple(self):
        """The defect is dishonesty, not wordiness."""
        soft = rule6_filler("We are rightsizing the team.")[0]
        plain = rule6_filler("We are firing eight people.")[0]
        self.assertLess(soft, plain)

    def test_clean_text_scores_ten(self):
        self.assertEqual(rule6_filler("The index is missing. Add it.")[0], 10.0)

    def test_rate_is_per_100_words(self):
        """One hit should cost less in a long answer than a short one."""
        short = rule6_filler("In order to run it, check the log.")[0]
        long = rule6_filler("In order to run it, check the log. " + "word " * 200)[0]
        self.assertGreater(long, short)


if __name__ == "__main__":
    unittest.main(verbosity=2)
