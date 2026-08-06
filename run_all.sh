#!/bin/bash
# Full re-run on the v2 24-prompt set. Subscription providers, no per-token cost.
# The hermes backend forces --safe-mode: no persona, no skills, no memory, no
# tools. Without it you are benchmarking the maintainer's agent, not the model.
cd ~/projects/readability-eval
run() {
  python3 -m readability_eval.run --backend hermes \
    --judge-model claude-opus-5 --judge-provider anthropic --judge-reasoning low \
    --workers 4 --condition "${3:-default}" \
    --model "$1" --provider "$2" \
    --label "$1$( [ -n "$3" ] && echo "__$3" )"
}
run claude-opus-5    anthropic    > /tmp/v3_opus.log  2>&1 &
run gpt-5.6-sol      openai-codex > /tmp/v3_gpt.log   2>&1 &
run grok-4.5         xai-oauth    > /tmp/v3_grok.log  2>&1 &
run gemini-3.5-flash google       > /tmp/v3_gem.log   2>&1 &
wait
run claude-fable-5     anthropic  > /tmp/v3_fable.log 2>&1 &
run moonshotai/kimi-k3 openrouter > /tmp/v3_kimi.log  2>&1 &
run gemini-3.6-flash   google     > /tmp/v3_gem36.log 2>&1 &
wait
echo done
