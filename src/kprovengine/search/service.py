from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .analytics import SearchAnalyticsRecorder
from .index import build_index, load_index
from .query import parse_search_query
from .ranker import rank_documents


class SearchService:
    def __init__(self, index_path: Path, analytics_path: Path | None = None) -> None:
        self.index_path = index_path
        self.analytics = SearchAnalyticsRecorder(analytics_path)

    def rebuild_index(self, runs_dir: Path, *, strict: bool = True) -> int:
        docs = build_index(runs_dir, self.index_path, strict=strict)
        return len(docs)

    def search(self, raw_query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        start = time.perf_counter()
        self.analytics.query_submitted(raw_query)

        query = parse_search_query(raw_query)
        documents = load_index(self.index_path)
        ranked = rank_documents(query, documents, limit=limit)

        latency_ms = int((time.perf_counter() - start) * 1000)
        top_score = ranked[0].score if ranked else None

        self.analytics.results_returned(
            raw_query,
            result_count=len(ranked),
            latency_ms=latency_ms,
            top_score=top_score,
        )
        if not ranked:
            self.analytics.zero_results(raw_query, latency_ms)

        return [_result_to_dict(result) for result in ranked]

    def record_selection(self, raw_query: str, doc_id: str, score: float, *, latency_ms: int | None = None) -> None:
        self.analytics.selected_result(raw_query, doc_id, score, latency_ms=latency_ms)


def _result_to_dict(result: Any) -> dict[str, Any]:
    document = result.document
    return {
        "rank": result.rank,
        "score": result.score,
        "score_explanation": [
            {"reason": component.reason, "points": component.points}
            for component in result.explanation.components
        ],
        "doc_id": document.doc_id,
        "run_id": document.run_id,
        "artifact_sha256": document.artifact_sha256,
        "source_revision": document.source_revision,
        "timestamp": document.timestamp,
        "artifact_type": document.artifact_type,
        "builder_id": document.builder_id,
        "artifact_rel_path": document.artifact_rel_path,
        "artifact_path": document.artifact_path,
        "provenance_path": document.provenance_path,
        "sbom_path": document.sbom_path,
        "hashes_path": document.hashes_path,
        "summary_path": document.summary_path,
        "policy_tags": list(document.policy_tags),
        "summary_text": document.summary_text,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kprovengine.search",
        description="Deterministic local search over kprovengine evidence bundles.",
    )
    parser.add_argument("--runs", default="runs", help="Directory containing run folders. Default: runs")
    parser.add_argument(
        "--index",
        default=None,
        help="Path to deterministic search JSONL index. Default: <runs>/search-index.jsonl",
    )
    parser.add_argument("--query", required=True, help="Search query string.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results. Default: 10")
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Force index rebuild from run artifacts before searching.",
    )
    parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fail on malformed run artifacts when rebuilding the index.",
    )
    parser.add_argument(
        "--analytics-log",
        default=None,
        help="Optional JSONL path for local search analytics events.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)

    runs_dir = Path(ns.runs)
    index_path = Path(ns.index) if ns.index else (runs_dir / "search-index.jsonl")
    analytics_path = Path(ns.analytics_log) if ns.analytics_log else None

    service = SearchService(index_path=index_path, analytics_path=analytics_path)

    if ns.rebuild_index or not index_path.is_file():
        indexed_docs = service.rebuild_index(runs_dir, strict=bool(ns.strict))
    else:
        indexed_docs = len(load_index(index_path))

    results = service.search(str(ns.query), limit=int(ns.limit))

    payload = {
        "index_path": str(index_path.resolve()),
        "indexed_documents": indexed_docs,
        "query": str(ns.query),
        "result_count": len(results),
        "results": results,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
