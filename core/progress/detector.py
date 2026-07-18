"""Detect loops that remain active without meaningful progress."""

from dataclasses import dataclass

from .invariant import ProgressInvariant


@dataclass
class ProgressObservation:
    valid_progress: bool
    reason: str


class NoProgressDetector:
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.no_progress_cycles = 0

    def observe(self, invariant: ProgressInvariant) -> ProgressObservation:
        if invariant.has_progress():
            self.no_progress_cycles = 0
            return ProgressObservation(True, "verified progress")

        self.no_progress_cycles += 1
        return ProgressObservation(
            False,
            f"no meaningful progress cycle {self.no_progress_cycles}",
        )

    def should_stop(self) -> bool:
        return self.no_progress_cycles >= self.threshold
