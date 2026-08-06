#!/bin/bash
# Claude models via --backend anthropic.
#
# Needs ANTHROPIC_API_KEY. Set ANTHROPIC_BASE_URL to route through a local
# proxy or gateway instead of the public API.
#
# The judge here is claude-opus-5, same family as the subjects, which is NOT
# neutral. Run rejudge.py with an OpenRouter judge before publishing a ranking.
set -euo pipefail
cd "$(dirname "$0")"

run() {
  python3 -m readability_eval.run \
    --backend anthropic --model "$1" \
    --judge-model claude-opus-5 --judge-backend anthropic \
    --workers 3 --condition "${2:-default}" \
    --label "$1$( [ -n "${2:-}" ] && echo "__$2" )"
}
for m in claude-opus-5 claude-opus-4-6 claude-sonnet-4-6 claude-haiku-4-5; do
  run "$m"       > "/tmp/c_${m}.log"       2>&1
  run "$m" brief > "/tmp/c_${m}_brief.log" 2>&1
done
python3 -m readability_eval.report
