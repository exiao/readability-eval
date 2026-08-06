"""Model callers.

Two backends, both RAW: one HTTP call to the model, a plain system prompt, and
no tools. That is the whole point of this eval — it scores the model itself, not
a harness wrapped around it.

  openrouter  — anyone can run this, costs money. Used for every non-Anthropic
                model.
  anthropic   — the maintainer's local billing proxy, which forwards to the
                Anthropic subscription. Used for Claude models.

WHY THERE IS NO `hermes` BACKEND ANYMORE
----------------------------------------
An earlier version shelled out to `hermes chat`. That is the maintainer's
personal agent, not a bare model: it loads SOUL.md, AGENTS.md, memory, skills
and ~31 tools including a live terminal. Every score produced that way was
invalid. Models read the maintainer's actual git repos and answered questions
that were never asked, in a house style learned from a persona file.

`--safe-mode` does NOT fix this. Per the Hermes docs it disables *user
customizations* for troubleshooting; the agent, its system prompt and its full
toolset remain. `-z/--oneshot` states outright that "tools, memory, rules, and
AGENTS.md in the CWD are loaded as normal." There is no CLI flag that yields a
bare model, by design — the CLI *is* the agent.

`probe_contamination` below is the guard, and `run.py` calls it before every
run. It is cheap and it would have caught the mistake immediately.
"""
import json
import os
import urllib.error
import urllib.request

SYSTEM = "You are a helpful assistant."
PROXY_URL = "http://127.0.0.1:18801/v1/messages"


def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{url} -> HTTP {e.code}: {e.read()[:300]}") from None


def call_openrouter(model, prompt, timeout=300):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    d = _post("https://openrouter.ai/api/v1/chat/completions", {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "usage": {"include": True},
    }, {"Authorization": f"Bearer {key}",
        "Content-Type": "application/json"}, timeout)
    return {"text": d["choices"][0]["message"]["content"],
            "cost_usd": (d.get("usage") or {}).get("cost", 0.0)}


def call_anthropic(model, prompt, timeout=300, max_tokens=4000):
    """Anthropic via the maintainer's local billing proxy.

    No `tools` field and no top-level `system` field: the proxy 400s on the
    first and 429s on the second. The system instruction is folded into the
    user message instead, which keeps this call shape identical in spirit to
    the OpenRouter one.

    max_tokens must comfortably exceed the longest expected answer. Some
    prompts have a 750-word budget, and the model also emits `thinking` blocks
    that count against the cap — too low a cap returns content with a thinking
    block and no text at all.
    """
    d = _post(PROXY_URL, {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user",
                      "content": f"{SYSTEM}\n\n---\n\n{prompt}"}],
    }, {"Content-Type": "application/json"}, timeout)
    text = "".join(b.get("text", "") for b in d.get("content", [])
                   if b.get("type") == "text").strip()
    if not text:
        stop = d.get("stop_reason")
        raise RuntimeError(
            f"empty response from {model} (stop_reason={stop}): {str(d)[:200]}")
    return {"text": text, "cost_usd": 0.0}


def call(model, prompt, backend="openrouter", provider=None, reasoning=None):
    if backend == "anthropic":
        return call_anthropic(model, prompt)
    return call_openrouter(model, prompt)


PROBE = ("Please answer these three questions about yourself, briefly:\n"
         "1. Are any third-party tools or functions available to you in this "
         "conversation? If yes, name them. If no, say NONE.\n"
         "2. What model are you?\n"
         "3. Has any personal memory, skill file, or project document been "
         "provided to you here? yes or no.")


def probe_contamination(model, backend):
    """Fail loudly if the backend is an agent rather than a bare model.

    Returns the probe text on success, raises RuntimeError on contamination.
    Two full re-runs were thrown away for want of this check.

    A refusal is not contamination: some safety filters decline introspection
    questions ("what tools do you have") as probing. Both backends here build
    the HTTP body in this file with no `tools` field, so a refusal still tells
    us the call shape is clean — it just cannot be confirmed from the answer.
    """
    try:
        text = call(model, PROBE, backend)["text"]
    except RuntimeError as e:
        if "refusal" in str(e):
            return "(model refused the introspection probe; call shape is "
            "tool-less by construction)"
        raise
    low = text.lower()
    bad = [t for t in ("terminal", "read_file", "web_search", "browser_",
                       "execute_code", "delegate_task", "skill_view")
           if t in low]
    if bad:
        raise RuntimeError(
            f"CONTAMINATED backend={backend} model={model}: the model reports "
            f"tools {bad}. This is an agent, not a raw model; scores would be "
            f"invalid. Probe said:\n{text[:400]}")
    if "hermes agent" in low:
        raise RuntimeError(
            f"CONTAMINATED backend={backend} model={model}: model identifies "
            f"as Hermes Agent, so an agent system prompt is attached.")
    return text
