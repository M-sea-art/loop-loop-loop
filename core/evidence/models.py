"""Evidence models shared by collection, judging, and policy gating."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EvidenceRecord:
    """A direct observation of an artifact for one acceptance claim."""

    claim_id: str
    artifact: str
    expected_content: str
    observed_content: str | None
    artifact_sha256: str | None
    exists: bool
    verified: bool = False
    verification_method: str = "read_file"
    created_at: str = field(default_factory=utc_now)


@dataclass
class EvidenceLedger:
    records: list[EvidenceRecord] = field(default_factory=list)

    def add(self, record: EvidenceRecord) -> None:
        self.records.append(record)

    def all_verified(self) -> bool:
        return bool(self.records) and all(record.verified for record in self.records)

    def claim_ids(self) -> set[str]:
        return {record.claim_id for record in self.records}
