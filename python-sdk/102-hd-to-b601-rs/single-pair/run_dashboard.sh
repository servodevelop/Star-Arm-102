#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
# Opening the local dashboard does not connect the arms.
python -m stararm_rs_feedback.dashboard --root "$PWD" --port "${1:-8765}"
