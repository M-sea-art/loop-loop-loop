"""Detect loops that remain active without meaningful progress."""

from dataclasses import dataclass
import json
from pathlib import Path

from core.storage_lock import exclusive_file_lock
from .invariant import ProgressInvariant


@dataclass
class ProgressObservation:
    valid_progress: bool
    reason: str


class NoProgressDetector:
    def __init__(
        self, threshold: int = 3, path: str | Path | None = None
    ):
        if threshold < 1:
            raise ValueError("threshold must be at least one")
        self.threshold = threshold
        self.path = Path(path) if path else None
        self._cycles: dict[str, int] = {}
        with exclusive_file_lock(self.path):
            self._load()

    def _load(self) -> None:
        if self.path and self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self._cycles = {key: int(value) for key, value in payload.items()}

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self._cycles, sort_keys=True), encoding="utf-8"
        )
        temporary.replace(self.path)

    def observe(
        self, invariant: ProgressInvariant, goal_id: str = "default"
    ) -> ProgressObservation:
        with exclusive_file_lock(self.path):
            self._load()
            if invariant.has_progress():
                self._cycles[goal_id] = 0
                self._save()
                return ProgressObservation(True, "verified progress")

            self._cycles[goal_id] = self._cycles.get(goal_id, 0) + 1
            self._save()
        return ProgressObservation(
            False,
            f"no meaningful progress cycle {self._cycles[goal_id]}",
        )

    def should_stop(self, goal_id: str = "default") -> bool:
        with exclusive_file_lock(self.path):
            self._load()
            return self._cycles.get(goal_id, 0) >= self.threshold

    def cycles(self, goal_id: str = "default") -> int:
        with exclusive_file_lock(self.path):
            self._load()
            return self._cycles.get(goal_id, 0)
