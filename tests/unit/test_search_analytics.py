from __future__ import annotations

import json
from pathlib import Path

import pytest

from kprovengine.search.analytics import SearchAnalyticsRecorder, SearchEvent


def test_search_event_to_dict_serializes_optionals() -> None:
    event = SearchEvent(
        event_type="selected_result",
        query="sha256:abc",
        result_count=2,
        top_result_score=1.23456789,
        selected_doc_id="run-001:provenance.json",
        latency_ms=9,
    )

    payload = event.to_dict()
    assert payload == {
        "event_type": "selected_result",
        "query": "sha256:abc",
        "result_count": 2,
        "top_result_score": 1.234568,
        "selected_doc_id": "run-001:provenance.json",
        "latency_ms": 9,
    }


def test_analytics_recorder_writes_append_only_jsonl(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "search-analytics.jsonl"
    recorder = SearchAnalyticsRecorder(log_path)

    recorder.query_submitted("audit")
    recorder.results_returned("audit", result_count=1, latency_ms=4, top_score=91.25)
    recorder.selected_result("audit", "run-001:provenance.json", 91.25, latency_ms=5)
    recorder.zero_results("none", latency_ms=2)

    rows = [json.loads(raw) for raw in log_path.read_text(encoding="utf-8").splitlines() if raw.strip()]
    assert len(rows) == 5

    assert rows[0]["event_type"] == "query_submitted"
    assert rows[1]["event_type"] == "results_returned"
    assert rows[1]["result_count"] == 1
    assert rows[2]["event_type"] == "top_result_score"
    assert rows[2]["top_result_score"] == 91.25
    assert rows[3]["event_type"] == "selected_result"
    assert rows[3]["selected_doc_id"] == "run-001:provenance.json"
    assert rows[4]["event_type"] == "zero_results"
    assert rows[4]["result_count"] == 0


def test_analytics_recorder_noop_when_path_is_none() -> None:
    recorder = SearchAnalyticsRecorder(None)
    recorder.query_submitted("audit")
    recorder.results_returned("audit", result_count=0, latency_ms=1, top_score=None)
    recorder.zero_results("audit", latency_ms=1)
    recorder.selected_result("audit", "doc", 0.0, latency_ms=1)


def test_analytics_recorder_rejects_unknown_event_type(tmp_path: Path) -> None:
    recorder = SearchAnalyticsRecorder(tmp_path / "events.jsonl")
    with pytest.raises(ValueError, match="Unsupported analytics event type"):
        recorder._write(SearchEvent(event_type="unsupported", query="x"))
