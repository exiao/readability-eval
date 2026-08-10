"""Model callers.

Two backends, both RAW: one HTTP call to the model, a plain system prompt, and
no tools. That is the whole point of this eval: it scores the model itself, not
a harness wrapped around it.

  openrouter  the default, and all you need. Any model, one API key.
  anthropic   the Anthropic Messages API directly, for Claude models.

Both read their credentials from the environment:

  OPENROUTER_API_KEY    required for --backend openrouter
  ANTHROPIC_API_KEY     required for --backend anthropic
  ANTHROPIC_BASE_URL    optional, override the Anthropic endpoint. Point this
                        at a local proxy or gateway if you route Claude
                        traffic through one. Defaults to the public API.

WHY THERE IS NO AGENT BACKEND
-----------------------------
An earlier version of this eval shelled out to a coding-agent CLI. That is not
a bare model: such CLIs load a persona file, project docs, memory, skills and
a live toolset. Every score produced that way was invalid. Models read local
git repositories and answered questions that were never asked, in a house
style learned from a persona file.

"Safe mode" flags do not fix this. They typically disable *user
customizations* for troubleshooting while the agent, its system prompt and its
toolset remain. If the CLI is the agent, there is no flag that yields a bare
model.

`probe_contamination` below is the guard, and `run.py` calls it before every
run. It is cheap and it would have caught the mistake immediately.
"""
import json
import os
import re
import urllib.error
import urllib.request

SYSTEM = "You are a helpful assistant."

BACKENDS = ("openrouter", "anthropic")

ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL",
                                    "https://api.anthropic.com").rstrip("/")
ANTHROPIC_VERSION = "2023-06-01"

# USD per million tokens, (input, output). Used only to fill the cost column;
# matched by substring so dated model ids resolve. Unlisted models report 0.0
# rather than a guess. These go stale -- treat them as a rough comparison aid,
# not billing.
ANTHROPIC_RATES = {
    "opus": (15.0, 75.0),
    "sonnet": (3.0, 15.0),
    "haiku": (0.8, 4.0),
}


def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{url} -> HTTP {e.code}: {e.read()[:300]}") from None


def call_openrouter(model, prompt, timeout=300, reasoning=None):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "usage": {"include": True},
    }
    if reasoning:
        # OpenRouter normalises this across vendors. Worth setting explicitly:
        # comparing a model at default effort against one at high effort is
        # comparing two configurations, not two models.
        body["reasoning"] = {"effort": reasoning}
    d = _post("https://openrouter.ai/api/v1/chat/completions", body,
              {"Authorization": f"Bearer {key}",
               "Content-Type": "application/json"}, timeout)
    choice = (d.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    text = msg.get("content")
    if text is None:
        # A refusal, or a reasoning model that spent its budget thinking and
        # emitted no answer, returns content=null. Left unhandled this raises
        # AttributeError deep in the runner and takes down all 10 prompts for
        # that model; surface it as a per-prompt error instead.
        raise RuntimeError(
            f"{model} returned no content (finish_reason="
            f"{choice.get('finish_reason')}, refusal={msg.get('refusal')!r})")
    return {"text": text,
            "cost_usd": (d.get("usage") or {}).get("cost", 0.0)}


def call_anthropic(model, prompt, timeout=300, max_tokens=4000):
    """Anthropic Messages API.

    Set ANTHROPIC_BASE_URL to route through a local proxy or gateway; it
    defaults to the public API. ANTHROPIC_API_KEY is required unless the
    endpoint you point at handles auth itself.

    The system instruction is folded into the user message rather than sent as
    a top-level `system` field, which keeps this call shape identical in spirit
    to the OpenRouter one and works against proxies that reject that field.

    max_tokens must comfortably exceed the longest expected answer. Some
    prompts have a 750-word budget, and models may also emit `thinking` blocks
    that count against the cap — too low a cap returns a thinking block and no
    text at all.
    """
    headers = {"Content-Type": "application/json",
               "anthropic-version": ANTHROPIC_VERSION}
    # ANTHROPIC_API_KEY is the documented name; ANTHROPIC_TOKEN is accepted
    # because gateways and proxies commonly export it under that name, and
    # silently sending no credential produced a 401 that read like a proxy
    # fault rather than a missing variable.
    key = os.environ.get("ANTHROPIC_API_KEY") or \
        os.environ.get("ANTHROPIC_TOKEN")
    if key:
        headers["x-api-key"] = key
    d = _post(f"{ANTHROPIC_BASE_URL}/v1/messages", {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user",
                      "content": f"{SYSTEM}\n\n---\n\n{prompt}"}],
    }, headers, timeout)
    text = "".join(b.get("text", "") for b in d.get("content", [])
                   if b.get("type") == "text").strip()
    if not text:
        stop = d.get("stop_reason")
        raise RuntimeError(
            f"empty response from {model} (stop_reason={stop}): {str(d)[:200]}")
    return {"text": text, "cost_usd": _anthropic_cost(model, d.get("usage"))}


def _anthropic_cost(model, usage):
    """Dollar cost from the Messages API usage block.

    Anthropic returns token counts, not a price, so this multiplies by a
    published per-million rate. Runs used to report $0.0 for every Claude
    model, which made the cost column silently wrong rather than absent.

    Unknown models return 0.0 rather than guessing: a wrong number is worse
    than a missing one. Rates are USD per million tokens and go stale -- they
    are a convenience for comparing runs, not billing.
    """
    if not usage:
        return 0.0
    rate = next((v for k, v in ANTHROPIC_RATES.items() if k in model), None)
    if rate is None:
        return 0.0
    ins = usage.get("input_tokens", 0) + \
        usage.get("cache_creation_input_tokens", 0) + \
        usage.get("cache_read_input_tokens", 0)
    out = usage.get("output_tokens", 0)
    return round(ins / 1e6 * rate[0] + out / 1e6 * rate[1], 6)


def call(model, prompt, backend="openrouter", provider=None, reasoning=None):
    """Dispatch to a backend. Unknown names raise rather than silently routing.

    An earlier version fell through to OpenRouter for anything that was not
    "anthropic", so a stale --backend value would quietly bill and run against
    a different backend than the one requested.
    """
    if backend == "anthropic":
        return call_anthropic(model, prompt)
    if backend == "openrouter":
        return call_openrouter(model, prompt, reasoning=reasoning)
    raise ValueError(
        f"unknown backend {backend!r}; supported: {', '.join(BACKENDS)}")


PROBE = ("Please answer these three questions about yourself, briefly:\n"
         "1. Are any third-party tools or functions available to you in this "
         "conversation? If yes, name them. If no, say NONE.\n"
         "2. What model are you?\n"
         "3. Has any personal memory, skill file, or project document been "
         "provided to you here? yes or no.")


_DENIAL = re.compile(
    r"\b(none|no tools?|not have|don'?t have|do not have|no access|"
    r"without access|lack|am not|i'?m not|no third-party|no third-party)\b")

_TOOL_NAMES = ("terminal", "read_file", "web_search", "browser_",
               "execute_code", "delegate_task", "skill_view")


def _first_answer(text):
    """The answer to question 1, which is the only one that names tools.

    Scanning the whole reply is what made this check misfire: a clean model
    answering question 2 with "I am Claude, I am not a coding agent" tripped
    both the tool scan and the identity scan. Questions 2 and 3 invite the
    words the scan is looking for.
    """
    # Split on the model's own enumeration. Falls back to the whole text when
    # the model answers in prose, which is the conservative direction.
    parts = re.split(r"(?m)^\s*(?:2[.)]|\*\*?2[.)])", text, maxsplit=1)
    return parts[0]


def probe_contamination(model, backend):
    """Fail loudly if the backend is an agent rather than a bare model.

    Returns the probe text on success, raises RuntimeError on contamination.
    Two full re-runs were thrown away for want of this check.

    A refusal is not contamination: some safety filters decline introspection
    questions ("what tools do you have") as probing. Both backends here build
    the HTTP body in this file with no `tools` field, so a refusal still tells
    us the call shape is clean — it just cannot be confirmed from the answer.

    Tool names are only contamination when the model AFFIRMS them. The check
    used to substring-scan the entire reply, so "I have no terminal access and
    I am not a coding agent" -- the most explicitly clean answer possible --
    aborted the whole run before a single prompt. It now reads the answer to
    question 1 and ignores tool names that sit inside a denial.

    The bias stays toward false alarms: an ambiguous answer that names tools
    without a clear denial still fails. Wasting a run beats publishing scores
    from an agent.
    """
    try:
        text = call(model, PROBE, backend)["text"]
    except RuntimeError as e:
        if "refusal" in str(e):
            return "(model refused the introspection probe; call shape is "
            "tool-less by construction)"
        raise
    answer = _first_answer(text)
    low = answer.lower()
    named = [t for t in _TOOL_NAMES if t in low]
    if named and not _DENIAL.search(low):
        raise RuntimeError(
            f"CONTAMINATED backend={backend} model={model}: the model reports "
            f"tools {named}. This is an agent, not a raw model; scores would "
            f"be invalid. Probe said:\n{text[:400]}")
    whole = text.lower()
    if re.search(r"\b(i am|i'?m) an? (agent|coding agent)\b", whole) and \
            not re.search(r"\b(not|never) an? (agent|coding agent)\b", whole):
        raise RuntimeError(
            f"CONTAMINATED backend={backend} model={model}: the model "
            f"identifies as an agent, so an agent system prompt is attached.")
    return text
