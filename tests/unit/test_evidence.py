from __future__ import annotations

import sys
from pathlib import Path

from kprovengine.evidence.attestation import Attestation
from kprovengine.evidence.bundle import EvidenceBundleSpec
from kprovengine.evidence.human_review import HumanReview
from kprovengine.evidence.provenance import ProvenanceRecord
from kprovengine.evidence.toolchain import Toolchain


def test_evidence_bundle_spec_files() -> None:
    spec = EvidenceBundleSpec()
    files = spec.all_files()

    assert isinstance(files, tuple)
    assert "manifest.json" in files
    assert all(isinstance(f, str) for f in files)


def test_human_review_pending() -> None:
    review = HumanReview.pending()

    assert review.status == "PENDING"
    assert review.reviewer is None
    assert isinstance(review.timestamp, str)
    assert review.timestamp.endswith("Z")


def test_attestation_fields() -> None:
    a = Attestation(author="testuser", statement="approved")

    assert a.author == "testuser"
    assert "approved" in a.statement
    assert isinstance(a.timestamp, str)
    assert a.timestamp.endswith("Z")


def test_toolchain_basic() -> None:
    t = Toolchain.basic()

    assert hasattr(t, "python_version")
    assert hasattr(t, "platform")

    # sys.version typically does not include the literal word "Python".
    # Require a version-like token and that it matches the running interpreter.
    version_token = t.python_version.split()[0]
    assert "." in version_token
    assert version_token == sys.version.split()[0]

    assert isinstance(t.platform, str)
    assert t.packages is None  # V1: no packages list by default


def test_provenance_record_from_paths(tmp_path: Path) -> None:
    inputs = [tmp_path / "in.txt"]
    outputs = [tmp_path / "out.txt"]

    for p in inputs + outputs:
        p.write_text("dummy")

    pr = ProvenanceRecord.from_paths("run0", inputs, outputs)

    assert pr.run_id == "run0"
    assert str(inputs[0]) in pr.inputs
    assert str(outputs[0]) in pr.outputs
    assert isinstance(pr.timestamp, str)
    assert pr.timestamp.endswith("Z")
