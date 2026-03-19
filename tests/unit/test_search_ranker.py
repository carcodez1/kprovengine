from __future__ import annotations

from kprovengine.search.models import SearchDocument
from kprovengine.search.query import parse_search_query
from kprovengine.search.ranker import rank_documents


def _doc(
    *,
    doc_id: str,
    run_id: str,
    sha256: str,
    artifact_type: str,
    search_text: str,
    policy_tags: tuple[str, ...],
) -> SearchDocument:
    return SearchDocument(
        doc_id=doc_id,
        run_id=run_id,
        artifact_sha256=sha256,
        source_revision="abc123",
        timestamp="2026-01-01T00:00:00Z",
        artifact_type=artifact_type,
        builder_id="CPython/3.12.0:cli",
        artifact_rel_path=doc_id.split(":", 1)[1],
        artifact_path=f"/tmp/{doc_id}",
        provenance_path="/tmp/provenance.json",
        sbom_path="/tmp/sbom.json",
        hashes_path="/tmp/hashes.txt",
        summary_path="/tmp/run_summary.json",
        policy_tags=policy_tags,
        summary_text=search_text,
        search_text=search_text,
    )


def test_exact_sha_match_beats_fuzzy() -> None:
    exact = _doc(
        doc_id="run-001:provenance.json",
        run_id="run-001",
        sha256="abc999",
        artifact_type="provenance",
        search_text="run-001 provenance compliance evidence",
        policy_tags=("policy:compliance",),
    )
    fuzzy = _doc(
        doc_id="run-001:outputs/report.txt",
        run_id="run-001",
        sha256="zzz111",
        artifact_type="output",
        search_text="run-001 report evidence",
        policy_tags=("artifact_type:output",),
    )

    results = rank_documents(parse_search_query("sha256:abc999 evidence"), [fuzzy, exact], limit=5)

    assert [row.document.doc_id for row in results][0] == "run-001:provenance.json"
    reasons = {component.reason for component in results[0].explanation.components}
    assert "exact_sha256" in reasons


def test_audit_intent_boost_is_explained() -> None:
    audit_doc = _doc(
        doc_id="run-002:provenance.json",
        run_id="run-002",
        sha256="111aaa",
        artifact_type="provenance",
        search_text="run-002 provenance audit compliance",
        policy_tags=("policy:compliance",),
    )
    output_doc = _doc(
        doc_id="run-002:outputs/report.txt",
        run_id="run-002",
        sha256="222bbb",
        artifact_type="output",
        search_text="run-002 output audit",
        policy_tags=("artifact_type:output",),
    )

    results = rank_documents(parse_search_query("run:run-002 audit"), [output_doc, audit_doc], limit=5)

    assert results[0].document.doc_id == "run-002:provenance.json"
    top_reasons = {component.reason for component in results[0].explanation.components}
    assert "audit_intent_boost" in top_reasons
    assert "exact_run_id" in top_reasons
