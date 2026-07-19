"""Single writer conflict scenario."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from examples.runtime_reliability.scenarios import run_writer_conflict_case


def run():
    with TemporaryDirectory() as directory:
        return run_writer_conflict_case(directory).status


if __name__ == "__main__":
    print(run())
