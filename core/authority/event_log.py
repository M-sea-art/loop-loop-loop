"""Append-only authority event storage foundation."""

from pathlib import Path
from .models import AuthorityEvent


class AuthorityEventLog:
    def __init__(self, path: str):
        self.path = Path(path)

    def append(self, event: AuthorityEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json() + "\n")

    def read_all(self) -> list[str]:
        if not self.path.exists():
            return []
        return self.path.read_text(encoding="utf-8").splitlines()
