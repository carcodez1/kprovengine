from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

EvidenceMode = Literal["DISABLED", "ENABLED"]
HumanReviewStatus = Literal["PENDING", "APPROVED", "REJECTED"]


@dataclass(frozen=True)
class RunInputs:
    """
    Contract for a pipeline run.

    V1: 'sources' are accepted and recorded; no extraction guarantees are claimed.
    """

    sources: list[Path]
    output_dir: Path
    run_id: str | None = None
    evidence: EvidenceMode = "ENABLED"
    review_status: HumanReviewStatus = "PENDING"


@dataclass(frozen=True)
class RunResult:
    """
    Contract for run output.

    V1 scaffold: outputs are produced by the pipeline; semantics are intentionally conservative.
    Timestamps are UTC-aware.
    """

    run_id: str
    started_at: datetime
    finished_at: datetime
    run_dir: Path
    outputs: list[Path]
    evidence_dir: Path | None
    summary: dict[str, str]