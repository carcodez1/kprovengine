from __future__ import annotations


class KprovError(Exception):
    """Base exception for the kprovengine core."""


class ConfigError(KprovError):
    """Configuration or invocation error."""


class PipelineError(KprovError):
    """Pipeline execution error."""
