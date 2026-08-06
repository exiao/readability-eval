#!/bin/bash
# Full run: every model in MODELS on the default condition.
#
# Needs OPENROUTER_API_KEY. Claude models go through --backend anthropic, which
# needs ANTHROPIC_API_KEY (set ANTHROPIC_BASE_URL to route via a local proxy).
# Drop the anthropic block if you only have an OpenRouter key.
set -euo pipefail
cd "$(dirname "$0")"

COND="${1:-default}"
SUFFIX=$( [ "$COND" = default ] && echo "" || echo "__$COND" )

run() {  # run <backend> <model> <label>
  python3 -m readability_eval.run \
    --backend "$1" --model "$2" --label "$3$SUFFIX" \
    --condition "$COND" --workers 4 \
    > "/tmp/re_$3$SUFFIX.log" 2>&1 &
}

run openrouter google/gemini-3.5-flash gemini-3.5-flash
run openrouter openai/gpt-5.6-sol      gpt-5.6-sol
run openrouter x-ai/grok-4.5           grok-4.5
run openrouter moonshotai/kimi-k3      kimi-k3
wait

for m in claude-opus-5 claude-opus-4-6 claude-sonnet-4-6 claude-haiku-4-5; do
  run anthropic "$m" "$m"
done
wait

python3 -m readability_eval.report
