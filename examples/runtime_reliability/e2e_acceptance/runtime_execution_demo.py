"""Runtime Reliability v1 end-to-end execution demo."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.runtime_reliability.scenarios import (
    ScenarioResult as ExecutionResult,
    run_success_case as _run_success_case,
)


def run_success_case(workspace: str | Path | None = None) -> ExecutionResult:
    if workspace is not None:
        return _run_success_case(workspace)
    with TemporaryDirectory() as directory:
        return _run_success_case(directory)


if __name__ == "__main__":
    print(run_success_case())
