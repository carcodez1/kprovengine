from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """
    Execute CLI via module invocation to avoid PATH ambiguity.
    """
    return subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", *args],
        capture_output=True,
        text=True,
    )


def _parse_json_stdout(proc: subprocess.CompletedProcess[str]) -> dict:
    """
    Contract: success path prints ONLY JSON to stdout when default --format=json.
    """
    try:
        return json.loads(proc.stdout)
    except Exception as e:  # pragma: no cover
        raise AssertionError(
            "Expected valid JSON on stdout.\n"
            f"returncode={proc.returncode}\n"
            f"stdout={proc.stdout!r}\n"
            f"stderr={proc.stderr!r}"
        ) from e


def test_cli_runs(tmp_path: Path) -> None:
    # Arrange
    src = tmp_path / "in.txt"
    src.write_text("abc", encoding="utf-8")

    outdir = tmp_path / "runs"

    # Act
    proc = _run_cli(str(src), "--out", str(outdir), "--no-evidence")

    # Assert: deterministic exit and channels
    assert proc.returncode == 0, f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    assert proc.stderr == "", f"unexpected stderr: {proc.stderr!r}"

    payload = _parse_json_stdout(proc)

    # Locked JSON surface (V1)
    assert set(payload.keys()) == {"run_id", "run_dir", "outputs", "evidence"}

    run_id = payload["run_id"]
    run_dir = payload["run_dir"]
    outputs = payload["outputs"]
    evidence = payload["evidence"]

    assert isinstance(run_id, str) and run_id
    assert isinstance(run_dir, str) and run_dir
    assert isinstance(outputs, list)
    assert isinstance(evidence, bool)
    assert evidence is False

    # Deterministic output ordering (stable for automation)
    assert all(isinstance(p, str) for p in outputs)
    assert outputs == sorted(outputs)

    # run_dir must be under the requested --out base
    run_dir_path = Path(run_dir).resolve()
    outdir_path = outdir.resolve()
    assert str(run_dir_path).startswith(str(outdir_path)), (
        f"Expected run_dir under outdir.\n"
        f"run_dir={run_dir_path}\n"
        f"outdir={outdir_path}\n"
        f"payload={payload}"
    )


def test_cli_help() -> None:
    """
    Help text varies between argparse versions; assert semantics, not formatting.
    """
    proc = _run_cli("--help")
    assert proc.returncode == 0

    out = proc.stdout + proc.stderr
    assert "usage:" in out
    assert "--out" in out
    assert "--evidence" in out
    assert "--no-evidence" in out
    assert "--format" in out
    assert "--version" in out
