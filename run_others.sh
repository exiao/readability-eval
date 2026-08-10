#!/bin/bash
# Full 30-prompt runs for every non-Claude model, judged via the local proxy.
set -uo pipefail
cd "$(dirname "$0")"
set -a; . "$HOME/.hermes/.env"; set +a
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-http://127.0.0.1:18801}"
J=(--judge-model claude-opus-5 --judge-backend anthropic)
run() { python3 -m readability_eval.run --backend openrouter --model "$1" --label "$2" "${J[@]}" --workers 4 > "/tmp/re_$2.log" 2>&1; echo "$2 exit=$?"; }

for pair in \
  "openai/gpt-5.6-sol|gpt-5.6-sol" \
  "openai/gpt-5.6-terra|gpt-5.6-terra" \
  "openai/gpt-5.6-luna|gpt-5.6-luna" \
  "moonshotai/kimi-k3|kimi-k3" \
  "google/gemini-3.6-flash|gemini-3.6-flash" \
  "google/gemini-3.5-flash|gemini-3.5-flash" \
  "x-ai/grok-4.5|grok-4.5" \
  "z-ai/glm-5.2|glm-5.2" \
  "qwen/qwen3.8-max|qwen3.8-max" ; do
  run "${pair%|*}" "${pair#*|}"
done
python3 -m readability_eval.report
