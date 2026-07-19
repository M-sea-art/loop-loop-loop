"""Independent reviewer facade; it receives no writer mutation methods."""

from __future__ import annotations

from pathlib import Path

from core.runtime.goal_authority import ReviewerCapability


class ArtifactReviewer:
    def __init__(self, workspace: str | Path, capability: ReviewerCapability):
        self.workspace = Path(workspace).resolve()
        self._capability = capability

    def verify_artifact(self, event_id: str):
        # Import lazily to keep the reviewer facade independent of worker setup.
        from core.runtime.reliability_runtime import ReliabilityRuntime

        runtime = ReliabilityRuntime(self.workspace)
        return runtime._verify_artifact(event_id, self._capability)
