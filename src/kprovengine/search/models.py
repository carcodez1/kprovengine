from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchDocument:
    doc_id: str
    run_id: str
    artifact_sha256: str
    source_revision: str | None
    timestamp: str
    artifact_type: str
    builder_id: str
    artifact_rel_path: str
    artifact_path: str
    provenance_path: str
    sbom_path: str
    hashes_path: str
    summary_path: str
    policy_tags: tuple[str, ...]
    summary_text: str
    search_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "run_id": self.run_id,
            "artifact_sha256": self.artifact_sha256,
            "source_revision": self.source_revision,
            "timestamp": self.timestamp,
            "artifact_type": self.artifact_type,
            "builder_id": self.builder_id,
            "artifact_rel_path": self.artifact_rel_path,
            "artifact_path": self.artifact_path,
            "provenance_path": self.provenance_path,
            "sbom_path": self.sbom_path,
            "hashes_path": self.hashes_path,
            "summary_path": self.summary_path,
            "policy_tags": list(self.policy_tags),
            "summary_text": self.summary_text,
            "search_text": self.search_text,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SearchDocument:
        return cls(
            doc_id=str(payload["doc_id"]),
            run_id=str(payload["run_id"]),
            artifact_sha256=str(payload["artifact_sha256"]),
            source_revision=(None if payload.get("source_revision") is None else str(payload.get("source_revision"))),
            timestamp=str(payload["timestamp"]),
            artifact_type=str(payload["artifact_type"]),
            builder_id=str(payload["builder_id"]),
            artifact_rel_path=str(payload["artifact_rel_path"]),
            artifact_path=str(payload["artifact_path"]),
            provenance_path=str(payload["provenance_path"]),
            sbom_path=str(payload["sbom_path"]),
            hashes_path=str(payload["hashes_path"]),
            summary_path=str(payload["summary_path"]),
            policy_tags=tuple(str(tag) for tag in payload.get("policy_tags", [])),
            summary_text=str(payload.get("summary_text", "")),
            search_text=str(payload.get("search_text", "")),
        )


@dataclass(frozen=True)
class SearchQuery:
    raw: str
    terms: tuple[str, ...]
    sha256: str | None = None
    run_id: str | None = None
    commit: str | None = None
    artifact_type: str | None = None
    tag: str | None = None
    phrase: str | None = None
    audit_intent: bool = False


@dataclass(frozen=True)
class ScoreComponent:
    reason: str
    points: float


@dataclass(frozen=True)
class ScoreExplanation:
    final_score: float
    components: tuple[ScoreComponent, ...]


@dataclass(frozen=True)
class SearchResult:
    rank: int
    score: float
    explanation: ScoreExplanation
    document: SearchDocument


@dataclass(frozen=True)
class RelevanceJudgment:
    query_id: str
    doc_id: str
    relevance: int
