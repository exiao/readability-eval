"""The contamination probe must reject affirmations, not denials.

It substring-scanned the whole reply, so the most explicitly clean answer
possible -- "I have no terminal access and I am not a coding agent" -- aborted
the run before a single prompt. It must still catch a real agent, because two
full runs were once thrown away for want of this check.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readability_eval import providers


def probe(monkeypatch, reply):
    monkeypatch.setattr(providers, "call",
                        lambda *a, **k: {"text": reply, "cost_usd": 0.0})
    return providers.probe_contamination("m", "openrouter")


CLEAN = [
    # The exact shape the review named.
    "1. NONE\n2. I am Claude.\n3. no",
    "1. No, I have no terminal access and I am not a coding agent.\n"
    "2. Claude Opus\n3. no",
    "1. I don't have any tools available such as web_search or "
    "read_file.\n2. GPT\n3. no",
    "1. None. I cannot execute_code or browse.\n2. Gemini\n3. no",
    # Denial phrased without naming a tool at all.
    "1. NONE\n2. A large language model.\n3. No.",
]

CONTAMINATED = [
    "1. Yes: terminal, read_file, web_search.\n2. Claude\n3. yes",
    "1. I have access to execute_code and delegate_task.\n2. Opus\n3. no",
    "1. Available functions: skill_view, browser_navigate.\n2. X\n3. yes",
]


@pytest.mark.parametrize("reply", CLEAN)
def test_clean_model_passes(reply, monkeypatch):
    assert probe(monkeypatch, reply)


@pytest.mark.parametrize("reply", CONTAMINATED)
def test_agent_is_still_caught(reply, monkeypatch):
    with pytest.raises(RuntimeError, match="CONTAMINATED"):
        probe(monkeypatch, reply)


def test_agent_self_identification_still_caught(monkeypatch):
    with pytest.raises(RuntimeError, match="identifies as an agent"):
        probe(monkeypatch, "1. NONE\n2. I am an agent built on Claude.\n3. no")


def test_denying_agenthood_is_not_contamination(monkeypatch):
    assert probe(monkeypatch,
                 "1. NONE\n2. I am not an agent, just a model.\n3. no")


def test_ambiguous_answer_still_fails(monkeypatch):
    """Bias stays toward false alarms: naming tools with no denial fails."""
    with pytest.raises(RuntimeError, match="CONTAMINATED"):
        probe(monkeypatch, "1. terminal, web_search\n2. Claude\n3. no")


def test_tool_names_in_later_answers_do_not_trip_it(monkeypatch):
    """Questions 2 and 3 invite the vocabulary the scan looks for."""
    assert probe(monkeypatch,
                 "1. NONE\n"
                 "2. I am Claude. I am not a terminal or a coding agent, "
                 "and I have no web_search capability.\n"
                 "3. no")
