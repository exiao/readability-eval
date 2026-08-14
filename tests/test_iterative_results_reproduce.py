"""Committed iterative results must reproduce from the metrics code in HEAD.

The results in results/iterative/*.json were once generated before three
clause-counter fixes landed, so 27 of 36 stored checkpoints carried erosion
values HEAD could no longer produce, and the headline drift table in
METHODOLOGY.md described a run nobody could reproduce. This test replays every
saved `response` through the current metrics and fails if any stored value has
drifted, so the next metrics change forces a refresh instead of silently
invalidating the published numbers.
"""
import glob
import json
import os

import pytest

from readability_eval import iterate, metrics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(glob.glob(os.path.join(ROOT, "results", "iterative", "*.json")))


@pytest.mark.parametrize("path", FILES, ids=[os.path.basename(f) for f in FILES])
def test_stored_metrics_match_recompute(path):
    data = json.load(open(path))
    stale = []
    for traj in data["trajectories"]:
        for cp in traj["checkpoints"]:
            if "error" in cp:
                continue
            fresh = metrics.measure(cp["response"])
            for key, value in fresh.items():
                if cp.get(key) != value:
                    stale.append(
                        f"{traj['problem']} C{cp['checkpoint']} {key}: "
                        f"stored {cp.get(key)} != recomputed {value}")
    assert not stale, (
        f"{len(stale)} stored metric values no longer reproduce; re-run "
        f"readability_eval.iterate or recompute the file:\n" + "\n".join(stale))


@pytest.mark.parametrize("path", FILES, ids=[os.path.basename(f) for f in FILES])
def test_stored_summary_matches_recompute(path):
    data = json.load(open(path))
    fresh = iterate.summarise(data["trajectories"])
    stored = {k: v for k, v in data["summary"].items() if k in fresh}
    assert stored == fresh
