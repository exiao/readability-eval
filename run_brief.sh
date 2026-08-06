#!/bin/bash
# Brief-condition run: does "answer in 50 words or less" close the economy gap?
cd ~/projects/readability-eval
run() {
  python3 -m readability_eval.run --backend hermes \
    --judge-model claude-opus-5 --judge-provider anthropic --judge-reasoning low \
    --workers 6 --condition brief \
    --model "$1" --provider "$2" --label "$1__brief"
}
run claude-opus-5    anthropic  > /tmp/b_opus.log  2>&1 &
run grok-4.5         xai-oauth  > /tmp/b_grok.log  2>&1 &
run claude-fable-5   anthropic  > /tmp/b_fable.log 2>&1 &
run gemini-3.5-flash google     > /tmp/b_gem.log   2>&1 &
wait
echo done
