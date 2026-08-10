"""Anthropic traffic must go through ANTHROPIC_BASE_URL, and report real cost.

The endpoint has always been env-driven, but auth only read
ANTHROPIC_API_KEY, so an environment exporting ANTHROPIC_TOKEN sent no
credential and got a 401 that looked like a proxy fault. Cost was hardcoded
to 0.0, so every saved Claude run claimed it was free.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readability_eval import providers

USAGE = {"input_tokens": 1000, "output_tokens": 500,
         "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}


def fake_post(captured):
    def _post(url, body, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        return {"content": [{"type": "text", "text": "ok"}],
                "stop_reason": "end_turn", "usage": USAGE}
    return _post


def test_requests_go_to_the_configured_base_url(monkeypatch):
    cap = {}
    monkeypatch.setattr(providers, "_post", fake_post(cap))
    monkeypatch.setattr(providers, "ANTHROPIC_BASE_URL", "http://127.0.0.1:18801")
    providers.call_anthropic("claude-opus-5", "hi")
    assert cap["url"] == "http://127.0.0.1:18801/v1/messages"


def test_anthropic_token_is_accepted_as_credentials(monkeypatch):
    cap = {}
    monkeypatch.setattr(providers, "_post", fake_post(cap))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_TOKEN", "tok-123")
    providers.call_anthropic("claude-opus-5", "hi")
    assert cap["headers"]["x-api-key"] == "tok-123"


def test_api_key_wins_when_both_are_set(monkeypatch):
    cap = {}
    monkeypatch.setattr(providers, "_post", fake_post(cap))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-primary")
    monkeypatch.setenv("ANTHROPIC_TOKEN", "tok-secondary")
    providers.call_anthropic("claude-opus-5", "hi")
    assert cap["headers"]["x-api-key"] == "key-primary"


def test_cost_is_reported_not_zero(monkeypatch):
    monkeypatch.setattr(providers, "_post", fake_post({}))
    out = providers.call_anthropic("claude-opus-5", "hi")
    # 1000 in @ $15/M + 500 out @ $75/M
    assert out["cost_usd"] == pytest.approx(0.015 + 0.0375)
    assert out["cost_usd"] > 0


def test_cheaper_models_cost_less(monkeypatch):
    monkeypatch.setattr(providers, "_post", fake_post({}))
    opus = providers.call_anthropic("claude-opus-5", "hi")["cost_usd"]
    haiku = providers.call_anthropic("claude-haiku-4-5", "hi")["cost_usd"]
    assert haiku < opus


def test_unknown_model_reports_zero_rather_than_guessing(monkeypatch):
    monkeypatch.setattr(providers, "_post", fake_post({}))
    assert providers.call_anthropic("some-new-model", "hi")["cost_usd"] == 0.0


def test_missing_usage_block_is_not_an_error(monkeypatch):
    def _post(url, body, headers, timeout):
        return {"content": [{"type": "text", "text": "ok"}],
                "stop_reason": "end_turn"}
    monkeypatch.setattr(providers, "_post", _post)
    assert providers.call_anthropic("claude-opus-5", "hi")["cost_usd"] == 0.0
