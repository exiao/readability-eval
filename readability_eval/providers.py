"""Model callers.

Two backends:
  openrouter  — anyone can run this, costs money
  hermes      — routes through local Hermes CLI to whatever subscriptions/OAuth
                providers are configured, so the maintainer runs it for free

Same interface, so results are comparable.
"""
import json
import os
import subprocess
import urllib.request

HERMES = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/hermes")
SYSTEM = "You are a helpful assistant."


def call_openrouter(model, prompt, timeout=300):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "usage": {"include": True},
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    return {"text": d["choices"][0]["message"]["content"],
            "cost_usd": (d.get("usage") or {}).get("cost", 0.0)}


def call_hermes(model, prompt, provider=None, timeout=600):
    """Route through a local Hermes install (subscription/OAuth providers).

    Free for the maintainer. Contributors should use the openrouter backend.
    """
    cmd = [HERMES, "chat", "-Q", "-q", prompt, "-m", model]
    if provider:
        cmd += ["--provider", provider]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return {"text": p.stdout.strip(), "cost_usd": 0.0}


def call(model, prompt, backend="openrouter", provider=None):
    if backend == "hermes":
        return call_hermes(model, prompt, provider)
    return call_openrouter(model, prompt)
