from __future__ import annotations

import os
import platform
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["Toolchain"]


@dataclass(frozen=True)
class Toolchain:
    python_version: str          # "3.12.12"
    python_implementation: str   # "CPython"
    platform_system: str         # "Darwin" / "Linux"
    platform_release: str        # "23.3.0" etc (OS-dependent, but fine)
    platform_machine: str        # "arm64" / "x86_64"
    packages: Mapping[str, str] | None = None

    @classmethod
    def basic(cls) -> Toolchain:
        v = sys.version_info
        return cls(
            python_version=f"{v.major}.{v.minor}.{v.micro}",
            python_implementation=platform.python_implementation(),
            platform_system=platform.system(),
            platform_release=platform.release(),
            platform_machine=platform.machine(),
            packages=None,
        )

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "python_version": self.python_version,
            "python_implementation": self.python_implementation,
            "platform_system": self.platform_system,
            "platform_release": self.platform_release,
            "platform_machine": self.platform_machine,
        }
        if self.packages is not None:
            d["packages"] = dict(self.packages)
        return d

    def to_contract_dict(
        self,
        *,
        version: str,
        entrypoint: str = "cli",
        cwd: Path | None = None,
    ) -> dict[str, Any]:
        git = _git_metadata(cwd)
        return {
            "schema_version": "1",
            "kprovengine": {
                "version": version,
                "entrypoint": entrypoint,
            },
            "python": {
                "implementation": self.python_implementation,
                "version": self.python_version,
            },
            "platform": {
                "system": self.platform_system,
                "release": self.platform_release,
                "machine": self.platform_machine,
            },
            "runtime": {
                "in_container": _in_container(),
            },
            "git": git,
        }


def _in_container() -> bool:
    return Path("/.dockerenv").exists() or os.getenv("KUBERNETES_SERVICE_HOST") is not None


def _git_metadata(cwd: Path | None) -> dict[str, str | None]:
    workdir = cwd or Path.cwd()
    repo = _git_output(["git", "-C", str(workdir), "config", "--get", "remote.origin.url"])
    ref = _git_output(["git", "-C", str(workdir), "rev-parse", "--abbrev-ref", "HEAD"])
    sha = _git_output(["git", "-C", str(workdir), "rev-parse", "HEAD"])
    return {
        "repo": repo,
        "ref": ref,
        "sha": sha,
    }


def _git_output(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    return out or None
