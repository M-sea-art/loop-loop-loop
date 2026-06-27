#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/loop.py run "$ROOT"
elif command -v python >/dev/null 2>&1; then
  python scripts/loop.py run "$ROOT"
else
  py -3 scripts/loop.py run "$ROOT"
fi
