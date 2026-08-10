"""Regression coverage for fail-closed full-run orchestration."""
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent


class TestRunAll(unittest.TestCase):
    def test_child_failure_stops_before_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "python3"
            fake.write_text(
                "#!/bin/sh\n"
                "case \"$2\" in\n"
                "  readability_eval.run) exit \"${FAIL_CHILD:-0}\" ;;\n"
                "  readability_eval.report) printf report-ran >&2 ;;\n"
                "esac\n"
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env["PATH"] = f"{tmp}:{env['PATH']}"
            env["FAIL_CHILD"] = "7"
            proc = subprocess.run(
                ["bash", str(ROOT / "run_all.sh")],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("refusing to publish report", proc.stderr)
        self.assertNotIn("report-ran", proc.stderr)

    def test_pins_one_judge_for_all_subjects(self):
        script = (ROOT / "run_all.sh").read_text()
        self.assertIn('JUDGE_MODEL="claude-opus-5"', script)
        self.assertIn('JUDGE_BACKEND="anthropic"', script)
        self.assertEqual(script.count('--judge-model "$JUDGE_MODEL"'), 1)
        self.assertEqual(script.count('--judge-backend "$JUDGE_BACKEND"'), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
