from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict


class CliSuccessPayload(TypedDict):
    run_id: str
    run_dir: str
    outputs: list[str]
    evidence: bool


def _run_cli(*args: str, timeout_s: int = 15) -> subprocess.CompletedProcess[str]:
    """
    Execute CLI via module invocation to avoid PATH ambiguity.
    """
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    # If you want warnings to fail builds, set this to "error" instead.
    env.setdefault("PYTHONWARNINGS", "ignore")

    return subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", *args],
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
    )


def _parse_success_json(proc: subprocess.CompletedProcess[str]) -> CliSuccessPayload:
    """
    Contract: success prints ONLY JSON to stdout in default --format=json.
    """
    try:
        raw: Any = json.loads(proc.stdout)
    except Exception as e:  # pragma: no cover
        raise AssertionError(
            "Expected valid JSON on stdout.\n"
            f"returncode={proc.returncode}\n"
            f"stdout={proc.stdout!r}\n"
            f"stderr={proc.stderr!r}"
        ) from e

    if not isinstance(raw, dict):
        raise AssertionError(f"Expected JSON object, got {type(raw)}: {raw!r}")

    required = {"run_id", "run_dir", "outputs", "evidence"}
    if set(raw.keys()) != required:
        raise AssertionError(f"Unexpected JSON keys. expected={required} got={set(raw.keys())}")

    # Validate types explicitly (strict, audit-friendly)
    run_id = raw["run_id"]
    run_dir = raw["run_dir"]
    outputs = raw["outputs"]
    evidence = raw["evidence"]

    if not isinstance(run_id, str) or not run_id:
        raise AssertionError(f"run_id invalid: {run_id!r}")
    if not isinstance(run_dir, str) or not run_dir:
        raise AssertionError(f"run_dir invalid: {run_dir!r}")
    if not isinstance(outputs, list) or not all(isinstance(p, str) for p in outputs):
        raise AssertionError(f"outputs invalid: {outputs!r}")
    if not isinstance(evidence, bool):
        raise AssertionError(f"evidence invalid: {evidence!r}")

    return CliSuccessPayload(run_id=run_id, run_dir=run_dir, outputs=outputs, evidence=evidence)


def test_cli_runs_success_contract(tmp_path: Path) -> None:
    src = tmp_path / "in.txt"
    src.write_text("abc", encoding="utf-8")

    outdir = tmp_path / "runs"

    proc = _run_cli(str(src), "--out", str(outdir), "--no-evidence")

    assert proc.returncode == 0, f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    assert proc.stderr == "", f"unexpected stderr: {proc.stderr!r}"

    payload = _parse_success_json(proc)

    assert payload["evidence"] is False

    # Deterministic ordering (V1 contract decision)
    assert payload["outputs"] == sorted(payload["outputs"])

    # run_dir must be under requested base
    run_dir_path = Path(payload["run_dir"]).resolve()
    outdir_path = outdir.resolve()
    assert str(run_dir_path).startswith(str(outdir_path)), (payload, run_dir_path, outdir_path)


def test_cli_help_semantics() -> None:
    proc = _run_cli("--help")
    assert proc.returncode == 0
    out = proc.stdout + proc.stderr
    assert "usage:" in out
    for token in ("--out", "--evidence", "--no-evidence", "--format", "--version"):
        assert token in out


def test_cli_missing_source_is_nonzero() -> None:
    proc = _run_cli("--no-evidence")
    assert proc.returncode != 0
    # Minimal invariant: it must communicate an error somewhere.
    assert (proc.stdout + proc.stderr).strip() != ""
