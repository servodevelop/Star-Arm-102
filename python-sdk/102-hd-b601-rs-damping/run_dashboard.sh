#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
stararm_python="${STARARM_PYTHON:-$HOME/miniforge3/envs/lerobot/bin/python}"
if [[ ! -x "$stararm_python" ]]; then
  echo "找不到 lerobot Python，请设置 STARARM_PYTHON 为该环境的解释器路径。" >&2
  exit 1
fi
exec "$stararm_python" -u -m stararm_rs_damping.dashboard --root "$PWD" --port "${1:-8767}"
