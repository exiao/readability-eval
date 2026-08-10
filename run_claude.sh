#!/bin/bash
# Claude models via --backend anthropic.
#
# Endpoint comes from ANTHROPIC_BASE_URL and defaults to the public API. Point
# it at a local proxy or gateway to route all Claude traffic through one place:
#
#   export ANTHROPIC_BASE_URL=http://127.0.0.1:PORT
#
# Credentials: ANTHROPIC_API_KEY, or ANTHROPIC_TOKEN if your gateway exports
# that name. Omit both only when the endpoint handles auth itself.
#
# The judge here is claude-opus-5, same family as the subjects, which is NOT
# neutral. Run rejudge.py with a judge from another family before publishing a
# ranking. Keep the judge on this same backend so one endpoint sees all Claude
# traffic; routing only the judge elsewhere splits a run across two providers.
set -euo pipefail
cd "$(dirname "$0")"

echo "anthropic endpoint: ${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"

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
