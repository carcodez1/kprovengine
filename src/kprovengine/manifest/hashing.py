from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = [
    "sha256_bytes",
    "sha256_file",
]


def sha256_bytes(data: bytes) -> str:
    """
    Compute the SHA-256 hex digest of the given bytes.

    Args:
        data: raw bytes to hash.

    Returns:
        A 64-character lowercase hex string.
    """
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: str | Path) -> str:
    """
    Compute the SHA-256 hex digest for a file.

    Args:
        path: filesystem path to read.

    Returns:
        A 64-character lowercase hex string.

    Raises:
        FileNotFoundError: if the path does not exist.
        PermissionError: if reading is not permitted.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Not a file: {p}")

    h = hashlib.sha256()
    with p.open("rb") as fp:
        for chunk in iter(lambda: fp.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()