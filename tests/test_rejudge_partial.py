"""`rejudge --write` must refuse a partial rewrite.

If some judge calls fail, the successful prompts get the new judge's scores
while the failed ones keep the old judge's, and the summary is relabelled with
the new judge alone. The file then claims a clean judge swap but silently
mixes two judges, which is the exact contamination this tool measures.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(script):
    return subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                          capture_output=True, text=True)


HARNESS = """
import json, os, sys
sys.path.insert(0, {root!r})
import readability_eval.rejudge as rj

FAIL_IDS = {fail!r}

def fake_one(r, jm, jb, jp):
    if r["id"] in FAIL_IDS:
        return r["id"], None, "simulated API timeout"
    return r["id"], dict(r["judge"]), None

rj.one = fake_one
sys.argv = ["rejudge", "--label", {label!r}, "--judge-model", "test/judge",
            "--write"]
try:
    rj.main()
except SystemExit as e:
    print("EXIT:", e.code)
    raise
"""


def _fixture():
    """Copy a real saved results file to a scratch label."""
    src = None
    for name in sorted(os.listdir(os.path.join(ROOT, "results"))):
        if not name.endswith(".json"):
            continue
        d = json.load(open(os.path.join(ROOT, "results", name)))
        if "summary" in d and len([r for r in d["runs"]
                                   if "error" not in r]) >= 2:
            src = os.path.join(ROOT, "results", name)
            break
    assert src, "no usable results fixture"
    label = "__rejudge_test__"
    dst = os.path.join(ROOT, "results", label + ".json")
    with open(src) as f:
        payload = f.read()
    open(dst, "w").write(payload)
    return label, dst, payload


def test_write_refuses_when_any_judge_call_fails():
    label, dst, before = _fixture()
    try:
        ids = [r["id"] for r in json.load(open(dst))["runs"]
               if "error" not in r]
        p = _run(HARNESS.format(root=ROOT, fail=[ids[0]], label=label))
        assert p.returncode != 0, p.stdout
        assert "refusing --write" in (p.stderr + p.stdout)
        # File must be byte-identical: no partial rewrite landed.
        assert open(dst).read() == before
    finally:
        os.remove(dst)


def test_write_succeeds_when_every_judge_call_succeeds():
    label, dst, before = _fixture()
    try:
        p = _run(HARNESS.format(root=ROOT, fail=[], label=label))
        assert p.returncode == 0, p.stderr
        d = json.load(open(dst))
        assert d["summary"]["judge_model"] == "test/judge"
    finally:
        os.remove(dst)
