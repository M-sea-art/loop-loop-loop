"""Evidence collection primitives for verified goal completion."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Evidence:
    claim_id: str
    artifact: str
    status: str = "unverified"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class EvidenceCollector:
    def collect(self, claim_id: str, artifact: str) -> Evidence:
        return Evidence(
            claim_id=claim_id,
            artifact=artifact,
            status="collected",
        )
