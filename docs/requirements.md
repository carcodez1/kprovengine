# Requirements (V1)

This document defines runtime and development requirements for **KProvEngine v1.x**.
Requirements are intentionally conservative to ensure reproducibility, CI parity, and stable dependency support.

---

## Python

- Supported: Python 3.11 – 3.12
- Rationale: These versions have stable wheels for common dependencies and are standard on GitHub Actions runners.
- Not targeted in V1: Python 3.13+ / 3.14 (may work locally, not guaranteed)

The project enforces this via:

    requires-python = ">=3.11,<3.13"

---

## Virtual Environments (macOS / Homebrew)

Homebrew Python distributions are externally managed (PEP 668).
Do not install project dependencies system-wide.

Recommended setup:

    brew install python@3.11
    /opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install -U pip
    python -m pip install -e ".[dev]"

Always install packages using python -m pip inside the virtual environment.

---

## OCR Engines

KProvEngine uses adapter boundaries. OCR engines are optional and may require OS-level dependencies.

### Tesseract (pytesseract adapter)

- Requires the tesseract binary installed on the host system.
- macOS (Homebrew):

    brew install tesseract

CI note: GitHub Actions runners do not include Tesseract by default.
V1 tests intentionally avoid requiring OCR engines.

### EasyOCR

- Python-based OCR engine
- May pull native dependencies via transitive packages
- Recommended for local development; not required for CI in V1

---

## LLM / Frameworks

- Local-first LLM usage is optional in V1 (e.g., Ollama)
- LangChain is permitted only inside adapters for:
  - prompt templating
  - output parsing
- No remote or cloud-based LLM APIs are used in V1

---

## Build & Packaging

Supported build workflow:

    python -m build

Expected outputs:

- dist/*.whl
- dist/*.tar.gz

---

## CI Compatibility

V1 CI workflows assume:

- Python 3.11
- No system OCR binaries installed
- Tests that do not require external AI services

This constraint is intentional to keep CI deterministic and low-risk.
