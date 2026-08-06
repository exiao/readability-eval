#!/bin/bash
# Claude models on the v3 WildChat prompt set, via the local billing proxy.
# Judge is claude-opus-5 on the same proxy: free, but NOT neutral for the Claude
# family. Run rejudge.py with an OpenRouter judge before publishing any ranking.
cd ~/projects/readability-eval
run() {
  python3 -m readability_eval.run \
    --backend anthropic --model "$1" \
    --judge-model claude-opus-5 --judge-backend anthropic \
    --workers 3 --condition "${2:-default}" \
    --label "$1$( [ -n "$2" ] && echo "__$2" )"
}
for m in claude-opus-5 claude-opus-4-6 claude-sonnet-4-6 claude-haiku-4-5; do
  run "$m"        > "/tmp/c_${m}.log"       2>&1
  run "$m" brief  > "/tmp/c_${m}_brief.log" 2>&1
done
echo done
