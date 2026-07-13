"""Evidence ledger for verifiable completion."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EvidenceRecord:
    claim: str
    artifact: str
    verified: bool = False
    created_at: str = datetime.utcnow().isoformat()


class EvidenceLedger:
    def __init__(self):
        self.records = []

    def add(self, record: EvidenceRecord):
        self.records.append(record)

    def all_verified(self) -> bool:
        return bool(self.records) and all(r.verified for r in self.records)
