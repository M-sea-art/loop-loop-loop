#!/usr/bin/env python3
"""Run the smallest complete LoopLoopLoop goal."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.loop.runtime import LoopRuntime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(tempfile.gettempdir()) / "looplooploop-simple-goal",
    )
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=True)

    result = LoopRuntime(args.workspace).run_once(Path(__file__).with_name("GOAL.md"))
    for event in result.trace:
        print(event)
    print(f"ARTIFACT={args.workspace / result.goal.target_path}")
    print(result.status)
    return 0 if result.status == "VERIFIED_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
