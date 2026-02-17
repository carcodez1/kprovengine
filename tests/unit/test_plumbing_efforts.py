from __future__ import annotations

from pytest import CaptureFixture


def test_config_module_executes_on_import() -> None:
    # Covers src/kprovengine/config.py (module top-level)
    import kprovengine.config as config  # noqa: F401

    # Minimal sanity: module should have at least one attribute besides dunders.
    public = [n for n in dir(config) if not n.startswith("_")]
    assert public, "expected config module to expose at least one public attribute"


def test_errors_module_exports_exception_types() -> None:
    # Covers src/kprovengine/errors.py
    import kprovengine.errors as errors

    # Accept common patterns; ensures module executes and exports something meaningful.
    exported = [
        getattr(errors, n) for n in dir(errors) if n.endswith("Error") or n.endswith("Exception")
    ]
    assert exported, "expected errors module to export at least one exception type"
    assert any(isinstance(obj, type) for obj in exported), "expected an exception class export"


def test_version_module_exports_non_empty_version_string() -> None:
    # Covers src/kprovengine/version.py
    import kprovengine.version as version

    # Don’t guess exact symbol; accept common conventions.
    candidates: list[object] = []
    for name in ("__version__", "VERSION", "version"):
        if hasattr(version, name):
            candidates.append(getattr(version, name))

    assert candidates, "expected a version attribute in kprovengine.version"
    # At least one value must be a non-empty string.
    assert any(isinstance(v, str) and v.strip() for v in candidates), (
        "expected non-empty version string"
    )


def test_smoke_output_capture_is_typed(capsys: CaptureFixture[str]) -> None:
    # This is a tiny typed capture to avoid Pylance 'Unknown' propagation regressions.
    print("ok")
    captured = capsys.readouterr()
    assert (captured.out + captured.err).strip() == "ok"
