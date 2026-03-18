from __future__ import annotations

import json
import subprocess
from pathlib import Path

from kprovengine.reporting import build_report_archive, render_report_html, write_report


def test_build_report_archive_with_git_metadata(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    artifact_path = repo / "notes.txt"
    artifact_path.write_text("alpha\nbeta\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "notes.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add notes"], cwd=repo, check=True, capture_output=True)

    manifest = {
        "report": {"title": "Test Evidence Report", "subtitle": "Synthetic manifest"},
        "subject": {"consultant": "Tester", "client": "Client", "matter": "Unit test"},
        "summary_notes": ["Git metadata should be captured when the artifact lives in a repository."],
        "artifacts": [
            {
                "id": "artifact_notes",
                "label": "Notes",
                "kind": "text_note",
                "path": str(artifact_path),
                "summary": "A tracked artifact for metadata enrichment.",
                "confidence": "high",
                "tags": ["local", "git"],
            },
            {
                "id": "bls_reference",
                "label": "BLS Reference",
                "kind": "official_source",
                "url": "https://www.bls.gov/ooh/computer-and-information-technology/computer-systems-analysts.htm",
                "summary": "Official wage baseline.",
                "confidence": "high",
                "tags": ["external"],
            },
        ],
        "claims": [
            {
                "id": "claim_exists",
                "label": "Tracked file exists",
                "summary": "The synthetic artifact exists and is committed.",
                "confidence": "high",
                "tags": ["claim"],
            }
        ],
        "cost_models": [
            {
                "id": "cost_floor",
                "label": "Conservative floor",
                "summary": "A synthetic cost model for rendering.",
                "confidence": "medium",
                "hours": 1.5,
                "rate": 100.0,
                "amount": 150.0,
                "tags": ["cost"],
            }
        ],
        "edges": [
            {"source": "artifact_notes", "target": "claim_exists", "kind": "supports"},
            {"source": "claim_exists", "target": "cost_floor", "kind": "informs"},
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    archive = build_report_archive(manifest_path)

    artifact = archive["artifacts"][0]
    assert artifact["sha256"]
    assert artifact["line_count"] == 2
    assert artifact["git"] is not None
    assert artifact["git"]["tracked"] is True
    assert artifact["git"]["commit_count"] == 1

    html = render_report_html(archive)
    assert "Interactive Evidence Map" in html
    assert "Test Evidence Report" in html

    html_path = tmp_path / "report.html"
    archive_path = tmp_path / "archive.json"
    write_report(manifest_path, html_path, archive_path)

    assert html_path.exists()
    assert archive_path.exists()
    assert "Test Evidence Report" in html_path.read_text(encoding="utf-8")
