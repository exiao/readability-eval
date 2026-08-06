"""Regression tests for scaffolding density (rule 7, deterministic half)."""
import unittest

from readability_eval.scaffold import count, score


class TestCount(unittest.TestCase):
    def test_ignores_code_fences(self):
        """A bash script is not scaffolding. Counting its comments as headings
        would punish exactly the answers that should use code."""
        t = "Run this:\n\n```bash\n# step one\n- not a bullet\n# step two\n```\n"
        self.assertEqual(count(t), (0, 0))

    def test_counts_standalone_bold_labels(self):
        t = "**Setup**\n\nInstall it.\n\n**Usage**\n\nRun it.\n"
        self.assertEqual(count(t)[0], 2)

    def test_inline_bold_is_not_a_heading(self):
        """Emphasis mid-sentence is normal writing, not a section label."""
        t = "The **fastest** option is a cache, though **redis** costs more.\n"
        self.assertEqual(count(t)[0], 0)

    def test_counts_ordered_and_unordered(self):
        t = "- one\n- two\n1. three\n2) four\n"
        self.assertEqual(count(t)[1], 4)

    def test_hyphen_in_prose_is_not_a_bullet(self):
        t = "It is a well-known trade-off, cost against speed.\n"
        self.assertEqual(count(t)[1], 0)


class TestScore(unittest.TestCase):
    def test_plain_prose_is_unpenalized(self):
        t = " ".join(["The cache expires after an hour."] * 20)
        self.assertEqual(score(t, 300)[0], 10.0)

    def test_modest_structure_is_free(self):
        """Three headings and a short list against a 300-word budget is
        ordinary formatting and must not cost anything."""
        t = "## A\n\ntext\n\n## B\n\n- one\n- two\n- three\n\n## C\n\ntext\n"
        self.assertEqual(score(t, 300)[0], 10.0)

    def test_report_theater_is_punished(self):
        t = ("## H\n" * 40) + ("- item\n" * 90)
        self.assertEqual(score(t, 300)[0], 0.0)

    def test_measured_against_budget_not_own_length(self):
        """The same answer is worse when the question was smaller. Scoring
        against its own length would call a bloated answer normally shaped."""
        t = ("## H\n\nsome text here\n" * 12)
        small = score(t, 60)[0]
        large = score(t, 800)[0]
        self.assertLess(small, large)

    def test_list_shaped_answer_to_list_shaped_ask(self):
        """A 10-item list against a 500-word budget is the right answer shape."""
        t = "Here are ten:\n\n" + "".join(f"- item {i}\n" for i in range(10))
        self.assertEqual(score(t, 500)[0], 10.0)

    def test_worst_offender_not_sum(self):
        """Heavy headings alone should score the same as heavy headings plus a
        clean body; the two penalties must not stack."""
        heads = "## H\n" * 40
        self.assertEqual(score(heads, 300)[0],
                         score(heads + "plain sentence.\n", 300)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
