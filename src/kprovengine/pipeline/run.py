# src/kprovengine/pipeline/run.py
from __future__ import annotations

import json
import logging
import secrets
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kprovengine.evidence.bundle import EvidenceBundleSpec
from kprovengine.evidence.human_review import HumanReview
from kprovengine.evidence.provenance import ProvenanceRecord
from kprovengine.evidence.toolchain import Toolchain
from kprovengine.manifest.hashing import sha256_file
from kprovengine.storage.layout import RunLayout
from kprovengine.types import RunInputs, RunResult
from kprovengine.version import __version__

logger = logging.getLogger(__name__)

RUN_SUMMARY_SCHEMA = "kprovengine.run_summary.v1"
SBOM_SCHEMA = "kprovengine.sbom.v1"


def run_pipeline(inputs: RunInputs) -> RunResult:
    """
    Deterministic runtime pipeline with full evidence bundle contract emission.
    """
    if not inputs.sources:
        raise ValueError("No source paths provided.")

    sources = sorted((Path(p) for p in inputs.sources), key=lambda p: str(p))
    for p in sources:
        if not p.is_file():
            raise FileNotFoundError(f"Source path not found: {p}")

    run_id = inputs.run_id or _gen_run_id()
    run_clock = _timestamp_from_run_id(run_id)
    started_at = run_clock
    finished_at = run_clock

    layout = RunLayout(inputs.output_dir, run_id)
    layout.ensure_run_dir()

    # Stage directories prevent SameFileError when inputs are already inside out_dir.
    stages_dir = layout.run_dir / "stages"
    normalized_dir = stages_dir / "normalized"
    parsed_dir = stages_dir / "parsed"
    extracted_dir = stages_dir / "extracted"
    rendered_dir = layout.run_dir / "outputs"  # stable final location for V1

    for d in (normalized_dir, parsed_dir, extracted_dir, rendered_dir):
        d.mkdir(parents=True, exist_ok=True)

    normalized = normalize_files(sources, normalized_dir)
    parsed = parse_files(normalized, parsed_dir)
    extracted = extract_records(parsed, extracted_dir)
    rendered = render_output(extracted, rendered_dir)

    stage_lineage = _stage_lineage(layout.run_dir, normalized, parsed, extracted, rendered)

    toolchain = Toolchain.basic().to_contract_dict(version=__version__, entrypoint="cli", cwd=Path.cwd())
    layout.toolchain_path.write_text(
        json.dumps(toolchain, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    prov = ProvenanceRecord.from_paths(
        run_id,
        sources,
        rendered,
        timestamp=_iso_utc(run_clock),
        stage_lineage=stage_lineage,
        toolchain_path=layout.toolchain_path.name,
    )
    layout.provenance_path.write_text(prov.to_json() + "\n", encoding="utf-8")

    review = HumanReview.pending(timestamp=_iso_utc(run_clock))
    layout.human_review_path.write_text(review.to_json() + "\n", encoding="utf-8")

    bundle_spec = EvidenceBundleSpec()
    required_bundle_names = sorted((*bundle_spec.all_files(), "run_summary.json"))

    summary: dict[str, Any] = {
        "schema": RUN_SUMMARY_SCHEMA,
        "run_id": run_id,
        "started_at": _iso_utc(started_at),
        "finished_at": _iso_utc(finished_at),
        "evidence": inputs.evidence,
        "review_status": inputs.review_status,
        "sources": [str(p) for p in sorted(sources, key=lambda p: str(p))],
        "outputs": _sorted_relative_paths(layout.run_dir, rendered),
        "stage_lineage": stage_lineage,
        "required_bundle_artifacts": required_bundle_names,
        "non_deterministic_fields": ["run_id"],
    }
    run_summary_path = layout.run_dir / "run_summary.json"
    run_summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Emit SBOM once before hashing to capture runtime artifact inventory.
    sbom_payload = _build_runtime_sbom(
        run_id=run_id,
        run_dir=layout.run_dir,
        rendered=rendered,
        required_bundle_names=required_bundle_names,
        hash_index={},
    )
    layout.sbom_path.write_text(json.dumps(sbom_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    hash_targets = _hash_targets(layout, rendered, run_summary_path, include_attestation=False)
    hash_index = _hash_index(layout.run_dir, hash_targets)

    # Re-render SBOM with resolved artifact hashes.
    sbom_payload = _build_runtime_sbom(
        run_id=run_id,
        run_dir=layout.run_dir,
        rendered=rendered,
        required_bundle_names=required_bundle_names,
        hash_index=hash_index,
    )
    layout.sbom_path.write_text(json.dumps(sbom_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    hash_index = _hash_index(layout.run_dir, hash_targets)

    attestation = _build_attestation(
        run_id=run_id,
        evidence_mode=inputs.evidence,
        hash_index=hash_index,
    )
    layout.attestation_path.write_text(attestation, encoding="utf-8")

    hash_targets = _hash_targets(layout, rendered, run_summary_path, include_attestation=True)
    hash_index = _hash_index(layout.run_dir, hash_targets)

    manifest_entries = _manifest_entries(hash_index)
    layout.manifest_path.write_text(
        json.dumps({"manifest": manifest_entries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest_hash = sha256_file(layout.manifest_path)
    _write_hashes_txt(
        hashes_path=layout.hashes_txt_path,
        manifest_entries=manifest_entries,
        manifest_hash=manifest_hash,
    )

    _validate_required_artifacts(layout)
    _validate_manifest_hash_consistency(layout, manifest_entries)

    return RunResult(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        run_dir=layout.run_dir,
        outputs=rendered,
        evidence_dir=layout.run_dir if inputs.evidence == "ENABLED" else None,
        summary=summary,
    )


def _gen_run_id() -> str:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{secrets.token_hex(3)}"


def _timestamp_from_run_id(run_id: str) -> datetime:
    token = run_id.split("-", 1)[0]
    try:
        parsed = datetime.strptime(token, "%Y%m%dT%H%M%SZ")
        return parsed.replace(tzinfo=UTC)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=UTC)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _relative_path(run_dir: Path, path: Path) -> str:
    return str(path.relative_to(run_dir).as_posix())


def _sorted_relative_paths(run_dir: Path, paths: Sequence[Path]) -> list[str]:
    return sorted(_relative_path(run_dir, p) for p in paths)


def _stage_lineage(
    run_dir: Path,
    normalized: Sequence[Path],
    parsed: Sequence[Path],
    extracted: Sequence[Path],
    rendered: Sequence[Path],
) -> list[dict[str, Any]]:
    return [
        {
            "stage": "normalize",
            "schema": "kprovengine.normalize.v1",
            "outputs": _sorted_relative_paths(run_dir, normalized),
        },
        {
            "stage": "parse",
            "schema": "kprovengine.parse.v1",
            "outputs": _sorted_relative_paths(run_dir, parsed),
        },
        {
            "stage": "extract",
            "schema": "kprovengine.extract.v1",
            "outputs": _sorted_relative_paths(run_dir, extracted),
        },
        {
            "stage": "render",
            "schema": "kprovengine.render.v1",
            "outputs": _sorted_relative_paths(run_dir, rendered),
        },
    ]


def _hash_targets(
    layout: RunLayout,
    rendered: Sequence[Path],
    run_summary_path: Path,
    *,
    include_attestation: bool,
) -> list[Path]:
    targets = [
        *rendered,
        layout.provenance_path,
        layout.human_review_path,
        run_summary_path,
        layout.toolchain_path,
        layout.sbom_path,
    ]
    if include_attestation:
        targets.append(layout.attestation_path)
    return sorted(targets, key=lambda p: str(p))


def _hash_index(run_dir: Path, paths: Sequence[Path]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in sorted(paths, key=lambda p: str(p)):
        if not path.is_file():
            raise RuntimeError(f"Expected hash target file missing: {path}")
        index[_relative_path(run_dir, path)] = sha256_file(path)
    return index


def _manifest_entries(hash_index: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"path": rel_path, "sha256": digest}
        for rel_path, digest in sorted(hash_index.items())
    ]


def _build_runtime_sbom(
    *,
    run_id: str,
    run_dir: Path,
    rendered: Sequence[Path],
    required_bundle_names: Sequence[str],
    hash_index: dict[str, str],
) -> dict[str, Any]:
    rendered_rel = _sorted_relative_paths(run_dir, rendered)
    bundle_components = sorted(
        name for name in required_bundle_names if name not in {"manifest.json", "hashes.txt"}
    )

    components: list[dict[str, Any]] = []
    for rel_path in sorted((*rendered_rel, *bundle_components)):
        kind = "pipeline_output" if rel_path.startswith("outputs/") else "evidence_artifact"
        entry: dict[str, Any] = {
            "path": rel_path,
            "kind": kind,
        }
        digest = hash_index.get(rel_path)
        if digest is not None:
            entry["sha256"] = digest
        components.append(entry)

    return {
        "schema": SBOM_SCHEMA,
        "run_id": run_id,
        "component_count": len(components),
        "components": components,
    }


def _build_attestation(
    *,
    run_id: str,
    evidence_mode: str,
    hash_index: dict[str, str],
) -> str:
    lines = [
        "# kprovengine Runtime Attestation",
        "",
        f"run_id: {run_id}",
        f"evidence_mode: {evidence_mode}",
        "",
        "This attestation binds runtime evidence artifacts to SHA-256 digests.",
        "",
    ]

    for rel_path, digest in sorted(hash_index.items()):
        lines.append(f"- {rel_path}: {digest}")
    lines.append("")

    return "\n".join(lines)


def _write_hashes_txt(
    *,
    hashes_path: Path,
    manifest_entries: Sequence[dict[str, str]],
    manifest_hash: str,
) -> None:
    rows = [(entry["path"], entry["sha256"]) for entry in manifest_entries]
    rows.append(("manifest.json", manifest_hash))
    rows = sorted(rows, key=lambda item: item[0])

    payload = "".join(f"{sha256}  {path}\n" for path, sha256 in rows)
    hashes_path.write_text(payload, encoding="utf-8", newline="\n")


def _validate_required_artifacts(layout: RunLayout) -> None:
    required = {
        layout.manifest_path,
        layout.provenance_path,
        layout.human_review_path,
        layout.toolchain_path,
        layout.hashes_txt_path,
        layout.attestation_path,
        layout.sbom_path,
        layout.run_dir / "run_summary.json",
    }

    missing = sorted(str(path) for path in required if not path.is_file())
    if missing:
        raise RuntimeError(f"Missing required artifacts: {missing}")


def _parse_hashes_txt(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        row = raw.strip()
        if not row:
            continue
        parts = row.split("  ", 1)
        if len(parts) != 2:
            raise RuntimeError(f"Invalid hashes.txt row: {row}")
        sha256, rel_path = parts
        entries[rel_path] = sha256
    return entries


def _validate_manifest_hash_consistency(
    layout: RunLayout,
    manifest_entries: Sequence[dict[str, str]],
) -> None:
    manifest_payload = json.loads(layout.manifest_path.read_text(encoding="utf-8"))
    on_disk_entries = manifest_payload.get("manifest")
    if not isinstance(on_disk_entries, list):
        raise RuntimeError("manifest.json missing 'manifest' list")

    expected_manifest = sorted(manifest_entries, key=lambda entry: entry["path"])
    actual_manifest = sorted(
        (
            {
                "path": str(entry.get("path", "")),
                "sha256": str(entry.get("sha256", "")),
            }
            for entry in on_disk_entries
        ),
        key=lambda entry: entry["path"],
    )
    if expected_manifest != actual_manifest:
        raise RuntimeError("manifest.json content does not match runtime hash index")

    hash_rows = _parse_hashes_txt(layout.hashes_txt_path)
    for entry in expected_manifest:
        path = entry["path"]
        digest = entry["sha256"]
        if path not in hash_rows:
            raise RuntimeError(f"hashes.txt missing entry for {path}")
        if hash_rows[path] != digest:
            raise RuntimeError(f"hashes.txt digest mismatch for {path}")

    manifest_hash = sha256_file(layout.manifest_path)
    if hash_rows.get("manifest.json") != manifest_hash:
        raise RuntimeError("manifest.json digest mismatch in hashes.txt")

    for entry in expected_manifest:
        rel_path = entry["path"]
        abs_path = layout.run_dir / rel_path
        if not abs_path.is_file():
            raise RuntimeError(f"Manifest references missing file: {rel_path}")
        if sha256_file(abs_path) != entry["sha256"]:
            raise RuntimeError(f"Manifest digest mismatch on disk for {rel_path}")


def normalize_files(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .normalize import normalize

    output_paths: list[Path] = []
    for p in sorted(inputs, key=lambda p: str(p)):
        out = outdir / p.name
        normalize(p, out)
        output_paths.append(out)
    return sorted(output_paths, key=lambda p: str(p))


def parse_files(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .parse import parse

    output_paths: list[Path] = []
    for p in sorted(inputs, key=lambda p: str(p)):
        out = outdir / p.name
        parse(p, out)
        output_paths.append(out)
    return sorted(output_paths, key=lambda p: str(p))


def extract_records(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .extract import extract

    output_paths: list[Path] = []
    for p in sorted(inputs, key=lambda p: str(p)):
        out = outdir / p.name
        extract(p, out)
        output_paths.append(out)
    return sorted(output_paths, key=lambda p: str(p))


def render_output(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .render import render

    output_paths: list[Path] = []
    for p in sorted(inputs, key=lambda p: str(p)):
        out = outdir / p.name
        render(p, out)
        output_paths.append(out)
    return sorted(output_paths, key=lambda p: str(p))
