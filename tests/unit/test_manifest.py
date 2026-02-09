# tests/unit/test_manifest.py
from __future__ import annotations

from pathlib import Path

from kprovengine.manifest.hashing import sha256_bytes
from kprovengine.manifest.manifest import build_manifest


def test_build_manifest_single(tmp_path: Path) -> None:
    p = tmp_path / "file.txt"
    content = b"test content"
    p.write_bytes(content)

    m = build_manifest([p])
    mdict = {e["path"]: e["sha256"] for e in m.to_dict()["manifest"]}

    assert mdict[str(p)] == sha256_bytes(content)


def test_build_manifest_multiple(tmp_path: Path) -> None:
    files: list[Path] = []
    expected_hashes: dict[str, str] = {}
    for i in range(3):
        f = tmp_path / f"f{i}.txt"
        data = f"data{i}".encode()
        f.write_bytes(data)
        files.append(f)
        expected_hashes[str(f)] = sha256_bytes(data)

    m = build_manifest(files)
    actual = {e["path"]: e["sha256"] for e in m.to_dict()["manifest"]}

    assert actual == expected_hashes