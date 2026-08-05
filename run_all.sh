#!/bin/bash
# Maintainer run: subscription/OAuth providers, no per-token cost.
# Contributors should use --backend openrouter instead.
cd ~/projects/readability-eval
R="python3 -m readability_eval.run --backend hermes --judge-model gemini-3.5-flash --judge-provider google --workers 6"

$R --model gpt-5.6-sol   --provider openai-codex --label gpt-5.6-sol   > /tmp/re_gpt.log 2>&1 &
$R --model grok-4.5      --provider xai-oauth    --label grok-4.5      > /tmp/re_grok.log 2>&1 &
$R --model gemini-3.5-flash --provider google    --label gemini-3.5-flash > /tmp/re_gem.log 2>&1 &
$R --model claude-fable-5 --provider anthropic   --label claude-fable-5 > /tmp/re_fable.log 2>&1 &
wait
# kimi k3 goes through OpenRouter (no subscription) — paid, but tiny
$R --model moonshotai/kimi-k3 --provider openrouter --label kimi-k3 > /tmp/re_kimi.log 2>&1
tail -3 /tmp/re_*.log
