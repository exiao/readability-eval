"""Regression tests for staccato detection (period-spam)."""
import unittest

from readability_eval.lexicon import score, staccato_runs


class TestStaccato(unittest.TestCase):
    def test_drill_sergeant_prose(self):
        t = "Little words. Short sentences. Cut the fat. Redo it."
        self.assertEqual(len(staccato_runs(t)), 1)

    def test_three_is_the_threshold(self):
        self.assertEqual(len(staccato_runs("Ship it. Test it.")), 0)
        self.assertEqual(len(staccato_runs("Ship it. Test it. Move on.")), 1)

    def test_questions_are_not_staccato(self):
        """Rhetorical question pairs are cadence the reader expects, and they
        wrecked the first version of this detector on real lesson plans."""
        t = "Shared history? Territory? A feeling in the heart?"
        self.assertEqual(len(staccato_runs(t)), 0)

    def test_exclamations_are_not_staccato(self):
        t = "Spread them wide! Now FLY! Soar through the garden!"
        self.assertEqual(len(staccato_runs(t)), 0)

    def test_list_items_are_not_staccato(self):
        t = "- Draw a circle.\n- Draw a square.\n- Draw a rectangle.\n"
        self.assertEqual(len(staccato_runs(t)), 0)

    def test_numbered_items_are_not_staccato(self):
        t = "1. Circle here.\n2. Square here.\n3. Triangle here.\n"
        self.assertEqual(len(staccato_runs(t)), 0)

    def test_headings_break_a_run(self):
        t = "Ship it.\n\n## Section\n\nTest it.\n\n## Other\n\nMove on.\n"
        self.assertEqual(len(staccato_runs(t)), 0)

    def test_joined_clauses_are_not_staccato(self):
        """The defect is refusing to join clauses, so a sentence that joins
        one cannot be part of a run."""
        t = "It is clunky, and slow. It is bad. We need better."
        self.assertEqual(len(staccato_runs(t)), 0)

    def test_normal_prose_is_clean(self):
        t = ("The cache expires hourly, which keeps memory flat while the "
             "index stays warm for the next request.")
        self.assertEqual(len(staccato_runs(t)), 0)

    def test_scores_as_slop(self):
        hits, b = score("Little words. Short sentences. Cut the fat.")
        self.assertIn("staccato", b)
        self.assertGreater(hits, 0)

    def test_short_answer_is_not_detonated(self):
        """A rate per 1000 words explodes on short text. One tic in a 50-word
        answer must not outweigh every vocabulary offence combined."""
        hits, _ = score("Ship it. Test it. Move on.")
        self.assertLessEqual(hits, 5.0)

    def test_cap_applies_only_to_staccato(self):
        """Banned vocabulary stays uncapped; only the structural tic is
        limited."""
        hits, b = score("We delve into the robust seamless realm.")
        self.assertGreater(hits, 100)

    def test_longer_text_dilutes_normally(self):
        short, _ = score("Ship it. Test it. Move on.")
        long, _ = score("Ship it. Test it. Move on. " + "filler word " * 300)
        self.assertLess(long, short)

    def test_quoted_text_is_stripped(self):
        """Prose *about* staccato must not score as staccato."""
        t = '> Ship it. Test it. Move on.\n'
        self.assertEqual(len(staccato_runs(t)), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
