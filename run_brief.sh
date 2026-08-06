#!/bin/bash
# Brief condition: does "answer in 50 words or less" close the economy gap?
# Same models as run_all.sh, so the two are directly comparable.
set -euo pipefail
cd "$(dirname "$0")"
exec ./run_all.sh brief
