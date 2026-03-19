from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import kprovengine.search.service as search_service
from kprovengine.search.models import (
    ScoreComponent,
    ScoreExplanation,
    SearchDocument,
    SearchQuery,
    SearchResult,
)


class DummyAnalytics:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def query_submitted(self, query: str) -> None:
        self.calls.append(("query_submitted", (query,), {}))

    def results_returned(self, query: str, result_count: int, latency_ms: int, top_score: float | None) -> None:
        self.calls.append(
            (
                "results_returned",
                (query, result_count, latency_ms, top_score),
                {},
            )
        )

    def zero_results(self, query: str, latency_ms: int) -> None:
        self.calls.append(("zero_results", (query, latency_ms), {}))

    def selected_result(self, query: str, doc_id: str, score: float, latency_ms: int | None = None) -> None:
        self.calls.append(("selected_result", (query, doc_id, score), {"latency_ms": latency_ms}))


def _doc() -> SearchDocument:
    return SearchDocument(
        doc_id="run-001:provenance.json",
        run_id="run-001",
        artifact_sha256="abc123",
        source_revision="deadbeef",
        timestamp="2026-01-01T00:00:00Z",
        artifact_type="provenance",
        builder_id="CPython/3.12.0:cli",
        artifact_rel_path="provenance.json",
        artifact_path="/tmp/run-001/provenance.json",
        provenance_path="/tmp/run-001/provenance.json",
        sbom_path="/tmp/run-001/sbom.json",
        hashes_path="/tmp/run-001/hashes.txt",
        summary_path="/tmp/run-001/run_summary.json",
        policy_tags=("policy:audit", "policy:compliance"),
        summary_text="summary",
        search_text="run-001 provenance",
    )


def _result() -> SearchResult:
    return SearchResult(
        rank=1,
        score=123.45,
        explanation=ScoreExplanation(
            final_score=123.45,
            components=(
                ScoreComponent(reason="exact_sha256", points=1000.0),
                ScoreComponent(reason="recency_tiebreak", points=0.001),
            ),
        ),
        document=_doc(),
    )


def test_service_search_happy_path_includes_explanation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = search_service.SearchService(index_path=tmp_path / "search-index.jsonl")
    analytics = DummyAnalytics()
    service.analytics = analytics  # type: ignore[assignment]

    parsed_query = SearchQuery(raw="sha256:abc123", terms=tuple(), sha256="abc123")

    monkeypatch.setattr(search_service, "parse_search_query", lambda raw: parsed_query)
    monkeypatch.setattr(search_service, "load_index", lambda path: [_doc()])
    monkeypatch.setattr(search_service, "rank_documents", lambda query, docs, limit: [_result()])

    results = service.search("sha256:abc123", limit=5)

    assert len(results) == 1
    first = results[0]
    assert first["doc_id"] == "run-001:provenance.json"
    assert first["score_explanation"][0]["reason"] == "exact_sha256"
    assert first["score_explanation"][1]["reason"] == "recency_tiebreak"
    assert first["policy_tags"] == ["policy:audit", "policy:compliance"]

    call_names = [row[0] for row in analytics.calls]
    assert call_names == ["query_submitted", "results_returned"]


def test_service_search_zero_results_emits_zero_event(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = search_service.SearchService(index_path=tmp_path / "search-index.jsonl")
    analytics = DummyAnalytics()
    service.analytics = analytics  # type: ignore[assignment]

    monkeypatch.setattr(search_service, "parse_search_query", lambda raw: SearchQuery(raw=raw, terms=tuple()))
    monkeypatch.setattr(search_service, "load_index", lambda path: [])
    monkeypatch.setattr(search_service, "rank_documents", lambda query, docs, limit: [])

    results = service.search("nothing")

    assert results == []
    call_names = [row[0] for row in analytics.calls]
    assert call_names == ["query_submitted", "results_returned", "zero_results"]


def test_service_rebuild_index_and_selection_forwarding(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = search_service.SearchService(index_path=tmp_path / "search-index.jsonl")
    analytics = DummyAnalytics()
    service.analytics = analytics  # type: ignore[assignment]

    captured: dict[str, Any] = {}

    def fake_build_index(runs_dir: Path, index_path: Path, *, strict: bool = True) -> list[SearchDocument]:
        captured["runs_dir"] = runs_dir
        captured["index_path"] = index_path
        captured["strict"] = strict
        return [_doc(), _doc()]

    monkeypatch.setattr(search_service, "build_index", fake_build_index)

    count = service.rebuild_index(tmp_path / "runs", strict=False)
    assert count == 2
    assert captured["strict"] is False

    service.record_selection("audit", "run-001:provenance.json", 91.0, latency_ms=12)
    assert analytics.calls[-1] == (
        "selected_result",
        ("audit", "run-001:provenance.json", 91.0),
        {"latency_ms": 12},
    )


class FakeService:
    def __init__(self, index_path: Path, analytics_path: Path | None) -> None:
        self.index_path = index_path
        self.analytics_path = analytics_path

    def rebuild_index(self, runs_dir: Path, *, strict: bool = True) -> int:
        self.rebuild_args = (runs_dir, strict)
        return 4

    def search(self, raw_query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        self.search_args = (raw_query, limit)
        return [{"doc_id": "run-001:provenance.json", "score_explanation": [{"reason": "x", "points": 1.0}]}]


def test_main_rebuild_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    created: dict[str, FakeService] = {}

    def fake_service_ctor(index_path: Path, analytics_path: Path | None = None) -> FakeService:
        instance = FakeService(index_path=index_path, analytics_path=analytics_path)
        created["instance"] = instance
        return instance

    monkeypatch.setattr(search_service, "SearchService", fake_service_ctor)

    rc = search_service.main(
        [
            "--runs",
            str(tmp_path / "runs"),
            "--query",
            "audit",
            "--rebuild-index",
            "--no-strict",
            "--limit",
            "2",
            "--analytics-log",
            str(tmp_path / "analytics.jsonl"),
        ]
    )

    assert rc == 0
    instance = created["instance"]
    assert instance.rebuild_args == (tmp_path / "runs", False)
    assert instance.search_args == ("audit", 2)

    payload = json.loads(capsys.readouterr().out)
    assert payload["indexed_documents"] == 4
    assert payload["result_count"] == 1


def test_main_existing_index_branch_uses_loaded_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    index_path = tmp_path / "runs" / "search-index.jsonl"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(search_service, "load_index", lambda path: [object(), object(), object()])

    class ExistingIndexService(FakeService):
        def rebuild_index(self, runs_dir: Path, *, strict: bool = True) -> int:  # pragma: no cover
            raise AssertionError("rebuild_index should not be called when index file already exists")

        def search(self, raw_query: str, *, limit: int = 10) -> list[dict[str, Any]]:
            return []

    monkeypatch.setattr(search_service, "SearchService", ExistingIndexService)

    rc = search_service.main(
        [
            "--runs",
            str(tmp_path / "runs"),
            "--index",
            str(index_path),
            "--query",
            "nohits",
        ]
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["indexed_documents"] == 3
    assert payload["result_count"] == 0
