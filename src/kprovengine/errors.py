from __future__ import annotations


class KProvError(Exception):
    """Base exception for KProvEngine."""


class ConfigError(KProvError):
    """Invalid configuration or arguments."""


class AdapterError(KProvError):
    """Adapter failure (OCR/LLM/etc)."""


class EvidenceError(KProvError):
    """Evidence bundle generation/validation failure."""