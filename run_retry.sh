#!/bin/bash
# Retry the three that timed out, serialized to avoid saturating the local CLI.
cd ~/projects/readability-eval
run() {
  python3 -m readability_eval.run --backend hermes \
    --judge-model gemini-3.5-flash --judge-provider google \
    --workers 3 --model "$1" --provider "$2" --label "$1"
}
run claude-opus-5    anthropic > /tmp/r_opus.log 2>&1
run grok-4.5         xai-oauth > /tmp/r_grok.log 2>&1
run gemini-3.5-flash google    > /tmp/r_gem.log  2>&1
echo done
