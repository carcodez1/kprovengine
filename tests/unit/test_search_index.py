from __future__ import annotations

from pathlib import Path

from kprovengine.pipeline.run import run_pipeline
from kprovengine.search.index import build_index, load_index
from kprovengine.types import RunInputs


def test_index_build_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("alpha\nbeta\n", encoding="utf-8")

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_pipeline(
        RunInputs(
            sources=[source],
            output_dir=runs_dir,
            run_id="20260101T000000Z-search",
            evidence="ENABLED",
        )
    )

    index_path = tmp_path / "search-index.jsonl"
    docs_first = build_index(runs_dir, index_path)
    first_payload = index_path.read_text(encoding="utf-8")

    docs_second = build_index(runs_dir, index_path)
    second_payload = index_path.read_text(encoding="utf-8")

    assert first_payload == second_payload
    assert docs_first == docs_second

    reloaded = load_index(index_path)
    assert reloaded == docs_first

    rel_paths = [doc.artifact_rel_path for doc in docs_first]
    assert rel_paths == sorted(rel_paths)

    artifact_types = {doc.artifact_type for doc in docs_first}
    assert {
        "manifest",
        "provenance",
        "human_review",
        "run_summary",
        "toolchain",
        "hashes",
        "sbom",
        "attestation",
        "output",
    }.issubset(artifact_types)

    for doc in docs_first:
        assert Path(doc.artifact_path).is_file()
        assert Path(doc.provenance_path).is_file()
        assert Path(doc.sbom_path).is_file()
        assert Path(doc.hashes_path).is_file()
        assert Path(doc.summary_path).is_file()
        assert doc.run_id == "20260101T000000Z-search"
