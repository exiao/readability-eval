"""Regression tests for chart data loading."""
import unittest

from readability_eval.chart import load


class TestLoad(unittest.TestCase):
    def test_default_load_mixes_sample_sizes(self):
        """Documents the hazard rather than asserting it away: the saved corpus
        genuinely holds 30-prompt and 5-prompt runs, and the unlimited load
        returns both. Callers plotting them on one axis must know."""
        rows = load()
        self.assertTrue(rows)
        self.assertIn("n", rows[0])

    def test_limit_makes_every_model_comparable(self):
        rows = load(limit=5)
        self.assertTrue(rows)
        self.assertEqual({r["n"] for r in rows}, {5},
                         "every row must cover the same prompt count")

    def test_limit_drops_models_with_too_few_runs(self):
        """A model that never answered 30 prompts cannot appear in a 30-prompt
        chart; silently averaging its 5 answers would be the original bug."""
        self.assertLessEqual(len(load(limit=30)), len(load(limit=5)))

    def test_rows_sorted_by_score(self):
        scores = [r["score"] for r in load(limit=5)]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
