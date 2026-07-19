"""Run all Runtime Reliability v1 acceptance scenarios."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.runtime_reliability.scenarios import (
    run_no_progress_case,
    run_revoke_case,
    run_success_case,
    run_writer_conflict_case,
)

SCENARIOS = [
    "success_case",
    "revoke_case",
    "no_progress_case",
    "writer_conflict_case",
]


def run():
    runners = {
        "success_case": run_success_case,
        "revoke_case": run_revoke_case,
        "no_progress_case": run_no_progress_case,
        "writer_conflict_case": run_writer_conflict_case,
    }
    results = {}
    for scenario, runner in runners.items():
        with TemporaryDirectory() as directory:
            results[scenario] = runner(directory)
            print(f"{scenario}: {results[scenario].status}")
    return results


if __name__ == "__main__":
    run()
