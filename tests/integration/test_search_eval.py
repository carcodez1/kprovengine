from __future__ import annotations

from pathlib import Path

from kprovengine.search.evaluate import evaluate_relevance, load_golden_fixture
from kprovengine.search.models import SearchDocument


def _doc(
    *,
    doc_id: str,
    run_id: str,
    sha256: str,
    artifact_type: str,
    search_text: str,
    tags: tuple[str, ...],
) -> SearchDocument:
    return SearchDocument(
        doc_id=doc_id,
        run_id=run_id,
        artifact_sha256=sha256,
        source_revision="deadbeef",
        timestamp="2026-01-01T00:00:00Z",
        artifact_type=artifact_type,
        builder_id="CPython/3.12.0:cli",
        artifact_rel_path=doc_id.split(":", 1)[1],
        artifact_path=f"/tmp/{doc_id}",
        provenance_path="/tmp/provenance.json",
        sbom_path="/tmp/sbom.json",
        hashes_path="/tmp/hashes.txt",
        summary_path="/tmp/run_summary.json",
        policy_tags=tags,
        summary_text=search_text,
        search_text=search_text,
    )


def test_offline_evaluation_is_deterministic() -> None:
    fixture = Path("tests/fixtures/search_golden.json")
    queries, judgments = load_golden_fixture(fixture)

    documents = [
        _doc(
            doc_id="run-001:provenance.json",
            run_id="run-001",
            sha256="aaa111",
            artifact_type="provenance",
            search_text="run-001 provenance compliance evidence",
            tags=("policy:compliance",),
        ),
        _doc(
            doc_id="run-001:sbom.json",
            run_id="run-001",
            sha256="bbb222",
            artifact_type="sbom",
            search_text="run-001 sbom compliance evidence",
            tags=("policy:compliance",),
        ),
        _doc(
            doc_id="run-001:outputs/report.txt",
            run_id="run-001",
            sha256="ccc333",
            artifact_type="output",
            search_text="run-001 output report",
            tags=("artifact_type:output",),
        ),
        _doc(
            doc_id="run-002:outputs/report.txt",
            run_id="run-002",
            sha256="ddd444",
            artifact_type="output",
            search_text="run-002 output report",
            tags=("artifact_type:output",),
        ),
    ]

    first = evaluate_relevance(documents, queries, judgments, k=3)
    second = evaluate_relevance(documents, queries, judgments, k=3)

    assert first == second
    assert first.query_count == 3
    assert first.precision_at_k == 0.555555
    assert first.mrr == 1.0
    assert first.ndcg_at_10 == 0.947609

    by_query = {row.query_id: row for row in first.per_query}
    assert by_query["q_sha"].precision_at_k == 0.333333
    assert by_query["q_compliance"].ndcg_at_10 == 0.842828
    assert by_query["q_output"].reciprocal_rank == 1.0
