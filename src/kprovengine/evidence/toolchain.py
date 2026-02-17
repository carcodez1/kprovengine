from __future__ import annotations

import platform
import sys
from collections.abc import Mapping
from dataclasses import dataclass
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
