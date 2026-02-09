# src/kprovengine/evidence/attestation.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

__all__ = ["Attestation"]


@dataclass(frozen=True)
class Attestation:
    author: str
    statement: str
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", _now_utc_iso())

    def to_dict(self) -> dict[str, Any]:
        return {"author": self.author, "statement": self.statement, "timestamp": self.timestamp}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
