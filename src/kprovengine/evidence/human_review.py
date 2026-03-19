# src/kprovengine/evidence/human_review.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

__all__ = ["HumanReview"]


@dataclass(frozen=True)
class HumanReview:
    status: str
    reviewer: str | None
    timestamp: str

    @classmethod
    def pending(cls, *, timestamp: str | None = None) -> HumanReview:
        return cls(status="PENDING", reviewer=None, timestamp=timestamp or _now_utc_iso())

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "reviewer": self.reviewer, "timestamp": self.timestamp}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
