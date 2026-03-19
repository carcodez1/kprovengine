from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EVENT_TYPES = frozenset(
    {
        "query_submitted",
        "results_returned",
        "zero_results",
        "top_result_score",
        "selected_result",
    }
)


@dataclass(frozen=True)
class SearchEvent:
    event_type: str
    query: str
    result_count: int | None = None
    top_result_score: float | None = None
    selected_doc_id: str | None = None
    latency_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_type": self.event_type,
            "query": self.query,
        }
        if self.result_count is not None:
            payload["result_count"] = int(self.result_count)
        if self.top_result_score is not None:
            payload["top_result_score"] = round(float(self.top_result_score), 6)
        if self.selected_doc_id is not None:
            payload["selected_doc_id"] = self.selected_doc_id
        if self.latency_ms is not None:
            payload["latency_ms"] = int(self.latency_ms)
        return payload


class SearchAnalyticsRecorder:
    """
    Local JSONL analytics recorder for deterministic experimentation readiness.
    """

    def __init__(self, path: Path | None) -> None:
        self._path = path

    def query_submitted(self, query: str) -> None:
        self._write(SearchEvent(event_type="query_submitted", query=query))

    def results_returned(self, query: str, result_count: int, latency_ms: int, top_score: float | None) -> None:
        self._write(
            SearchEvent(
                event_type="results_returned",
                query=query,
                result_count=result_count,
                latency_ms=latency_ms,
            )
        )
        if top_score is not None:
            self._write(
                SearchEvent(
                    event_type="top_result_score",
                    query=query,
                    top_result_score=top_score,
                    latency_ms=latency_ms,
                )
            )

    def zero_results(self, query: str, latency_ms: int) -> None:
        self._write(
            SearchEvent(
                event_type="zero_results",
                query=query,
                result_count=0,
                latency_ms=latency_ms,
            )
        )

    def selected_result(self, query: str, doc_id: str, score: float, latency_ms: int | None = None) -> None:
        self._write(
            SearchEvent(
                event_type="selected_result",
                query=query,
                selected_doc_id=doc_id,
                top_result_score=score,
                latency_ms=latency_ms,
            )
        )

    def _write(self, event: SearchEvent) -> None:
        if self._path is None:
            return
        if event.event_type not in EVENT_TYPES:
            raise ValueError(f"Unsupported analytics event type: {event.event_type}")

        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
        with self._path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)
