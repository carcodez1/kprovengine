from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kprovengine.manifest.hashing import sha256_file

from .models import SearchDocument

INDEX_SCHEMA = "kprovengine.search_index.v1"
REQUIRED_RUN_ARTIFACTS = (
    "manifest.json",
    "provenance.json",
    "human_review.json",
    "run_summary.json",
    "toolchain.json",
    "hashes.txt",
    "sbom.json",
    "attestation.md",
)

AUDIT_ARTIFACT_TYPES = frozenset(
    {
        "attestation",
        "hashes",
        "human_review",
        "manifest",
        "provenance",
        "run_summary",
        "sbom",
        "toolchain",
    }
)


def build_index(runs_dir: Path, index_path: Path, *, strict: bool = True) -> list[SearchDocument]:
    """
    Build deterministic JSONL index from pipeline run directories.
    """
    docs: list[SearchDocument] = []
    for run_dir in _iter_run_dirs(runs_dir):
        try:
            docs.extend(_build_documents_for_run(run_dir))
        except Exception:
            if strict:
                raise

    docs = sorted(docs, key=lambda d: (d.run_id, d.artifact_rel_path, d.doc_id))
    _write_jsonl(index_path, docs)
    return docs


def load_index(index_path: Path) -> list[SearchDocument]:
    if not index_path.is_file():
        return []

    docs: list[SearchDocument] = []
    for raw in index_path.read_text(encoding="utf-8").splitlines():
        row = raw.strip()
        if not row:
            continue
        payload = json.loads(row)
        docs.append(SearchDocument.from_dict(payload))

    return sorted(docs, key=lambda d: (d.run_id, d.artifact_rel_path, d.doc_id))


def _iter_run_dirs(runs_dir: Path) -> list[Path]:
    if not runs_dir.exists():
        return []
    return sorted((p for p in runs_dir.iterdir() if p.is_dir()), key=lambda p: p.name)


def _build_documents_for_run(run_dir: Path) -> list[SearchDocument]:
    required_paths = {name: run_dir / name for name in REQUIRED_RUN_ARTIFACTS}
    missing = sorted(name for name, path in required_paths.items() if not path.is_file())
    if missing:
        raise RuntimeError(f"Run directory missing required artifacts: {run_dir} {missing}")

    manifest = _load_json(required_paths["manifest.json"])
    run_summary = _load_json(required_paths["run_summary.json"])
    provenance = _load_json(required_paths["provenance.json"])
    toolchain = _load_json(required_paths["toolchain.json"])
    human_review = _load_json(required_paths["human_review.json"])

    manifest_entries = manifest.get("manifest")
    if not isinstance(manifest_entries, list):
        raise RuntimeError(f"Invalid manifest in {run_dir}")

    hash_rows = _parse_hashes_txt(required_paths["hashes.txt"])
    _validate_manifest_consistency(run_dir, manifest_entries, hash_rows)

    artifact_rows = [
        {
            "path": str(entry.get("path", "")).strip(),
            "sha256": str(entry.get("sha256", "")).strip().lower(),
        }
        for entry in manifest_entries
    ]
    artifact_rows.append(
        {
            "path": "manifest.json",
            "sha256": str(hash_rows.get("manifest.json", "")).strip().lower(),
        }
    )
    artifact_rows.append(
        {
            "path": "hashes.txt",
            "sha256": sha256_file(required_paths["hashes.txt"]).lower(),
        }
    )
    artifact_rows = sorted(artifact_rows, key=lambda item: item["path"])

    run_id = str(run_summary.get("run_id") or provenance.get("run_id") or run_dir.name)
    source_revision = _nested_get(toolchain, "git", "sha")
    builder_id = _builder_identity(toolchain)
    timestamp = str(run_summary.get("finished_at") or provenance.get("timestamp") or "1970-01-01T00:00:00Z")

    run_tags = _run_policy_tags(run_summary, human_review)
    run_summary_text = _run_summary_text(run_summary, provenance, toolchain)

    docs: list[SearchDocument] = []
    for entry in artifact_rows:
        rel_path = entry["path"]
        digest = entry["sha256"]
        if not rel_path or not digest:
            raise RuntimeError(f"Malformed manifest row in {run_dir}: {entry}")

        artifact_path = (run_dir / rel_path).resolve()
        artifact_type = _artifact_type(rel_path)

        policy_tags = sorted(
            {
                *run_tags,
                f"artifact_type:{artifact_type}",
                *(_audit_tags(artifact_type)),
            }
        )

        search_text = " ".join(
            [
                run_id,
                rel_path,
                artifact_type,
                digest,
                source_revision or "",
                builder_id,
                " ".join(policy_tags),
                run_summary_text,
            ]
        ).casefold()

        docs.append(
            SearchDocument(
                doc_id=f"{run_id}:{rel_path}",
                run_id=run_id,
                artifact_sha256=digest,
                source_revision=source_revision,
                timestamp=timestamp,
                artifact_type=artifact_type,
                builder_id=builder_id,
                artifact_rel_path=rel_path,
                artifact_path=str(artifact_path),
                provenance_path=str(required_paths["provenance.json"].resolve()),
                sbom_path=str(required_paths["sbom.json"].resolve()),
                hashes_path=str(required_paths["hashes.txt"].resolve()),
                summary_path=str(required_paths["run_summary.json"].resolve()),
                policy_tags=tuple(policy_tags),
                summary_text=run_summary_text,
                search_text=search_text,
            )
        )

    return docs


def _validate_manifest_consistency(
    run_dir: Path,
    manifest_entries: list[dict[str, Any]],
    hash_rows: dict[str, str],
) -> None:
    for entry in manifest_entries:
        rel_path = str(entry.get("path", "")).strip()
        digest = str(entry.get("sha256", "")).strip().lower()
        if hash_rows.get(rel_path) != digest:
            raise RuntimeError(f"hashes.txt mismatch for {run_dir / rel_path}")

        artifact_path = run_dir / rel_path
        if not artifact_path.is_file():
            raise RuntimeError(f"Manifest references missing file: {artifact_path}")
        if sha256_file(artifact_path).lower() != digest:
            raise RuntimeError(f"On-disk digest mismatch for {artifact_path}")

    manifest_digest = sha256_file(run_dir / "manifest.json").lower()
    if hash_rows.get("manifest.json") != manifest_digest:
        raise RuntimeError(f"manifest.json digest mismatch in hashes.txt for {run_dir}")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected object JSON in {path}")
    return payload


def _parse_hashes_txt(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        digest, rel_path = line.split("  ", 1)
        rows[rel_path.strip()] = digest.strip().lower()
    return rows


def _nested_get(payload: dict[str, Any], *keys: str) -> str | None:
    node: Any = payload
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return None if node is None else str(node)


def _builder_identity(toolchain: dict[str, Any]) -> str:
    implementation = _nested_get(toolchain, "python", "implementation") or "unknown-python"
    version = _nested_get(toolchain, "python", "version") or "unknown-version"
    entrypoint = _nested_get(toolchain, "kprovengine", "entrypoint") or "unknown-entry"
    return f"{implementation}/{version}:{entrypoint}"


def _run_policy_tags(run_summary: dict[str, Any], human_review: dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    evidence = str(run_summary.get("evidence", "UNKNOWN")).lower()
    review_status = str(human_review.get("status") or run_summary.get("review_status") or "unknown").lower()

    tags.add(f"evidence:{evidence}")
    tags.add(f"review:{review_status}")
    tags.add("contract:evidence_bundle")

    required = run_summary.get("required_bundle_artifacts")
    if isinstance(required, list):
        tags.add(f"contract_count:{len(required)}")

    return tags


def _artifact_type(rel_path: str) -> str:
    if rel_path.startswith("outputs/"):
        return "output"

    name = Path(rel_path).name
    mapping = {
        "attestation.md": "attestation",
        "hashes.txt": "hashes",
        "human_review.json": "human_review",
        "manifest.json": "manifest",
        "provenance.json": "provenance",
        "run_summary.json": "run_summary",
        "sbom.json": "sbom",
        "toolchain.json": "toolchain",
    }
    return mapping.get(name, Path(name).stem.replace("-", "_"))


def _audit_tags(artifact_type: str) -> set[str]:
    if artifact_type in AUDIT_ARTIFACT_TYPES:
        return {"policy:audit", "policy:compliance"}
    return set()


def _run_summary_text(
    run_summary: dict[str, Any],
    provenance: dict[str, Any],
    toolchain: dict[str, Any],
) -> str:
    sources = run_summary.get("sources") if isinstance(run_summary.get("sources"), list) else []
    outputs = run_summary.get("outputs") if isinstance(run_summary.get("outputs"), list) else []
    stages = provenance.get("stage_lineage") if isinstance(provenance.get("stage_lineage"), list) else []

    stage_names = [str(item.get("stage", "")) for item in stages if isinstance(item, dict)]
    git_sha = _nested_get(toolchain, "git", "sha") or ""
    git_ref = _nested_get(toolchain, "git", "ref") or ""

    parts = [
        str(run_summary.get("run_id", "")),
        str(run_summary.get("started_at", "")),
        str(run_summary.get("finished_at", "")),
        str(run_summary.get("review_status", "")),
        str(run_summary.get("evidence", "")),
        git_ref,
        git_sha,
        " ".join(sorted(str(x) for x in sources)),
        " ".join(sorted(str(x) for x in outputs)),
        " ".join(sorted(stage_names)),
    ]
    return " ".join(part for part in parts if part).strip()


def _write_jsonl(path: Path, docs: list[SearchDocument]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(doc.to_dict(), sort_keys=True, separators=(",", ":"))
        for doc in docs
    ]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    path.write_text(payload, encoding="utf-8", newline="\n")
