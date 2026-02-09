# src/kprovengine/evidence/toolchain.py
from __future__ import annotations

import platform
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

__all__ = ["Toolchain"]


@dataclass(frozen=True)
class Toolchain:
    python_version: str
    platform: str
    packages: Mapping[str, str] | None = None

    @classmethod
    def basic(cls) -> Toolchain:
        return cls(
            python_version=sys.version,
            platform=f"{platform.system()}-{platform.release()}-{platform.machine()}",
            packages=None,
        )

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"python_version": self.python_version, "platform": self.platform}
        if self.packages is not None:
            d["packages"] = dict(self.packages)
        return d