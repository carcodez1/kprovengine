# KProvEngine

[![CI](https://github.com/carcodez1/KProvEngine/actions/workflows/ci.yml/badge.svg)](https://github.com/carcodez1/KProvEngine/actions/workflows/ci.yml)
[![Security](https://github.com/carcodez1/KProvEngine/actions/workflows/security.yml/badge.svg)](https://github.com/carcodez1/KProvEngine/actions/workflows/security.yml)
[![Python](https://img.shields.io/badge/python-3.11–3.12-blue)](#python-version-policy-v1)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Scope](https://img.shields.io/badge/scope-V1%20locked-critical)](#governance--scope-lock)

KProvEngine is a **local-first provenance engine** for AI-assisted human workflows.

It converts unstructured artifacts into structured outputs while producing
**verifiable evidence of execution, toolchain disclosure, authorship, and
explicit human review**.

The project is intentionally conservative.
AI may assist extraction and structuring, but **humans remain the authority**.

This repository prioritizes correctness, traceability, and governance over
feature breadth.

---

## Design Goals

- Local-first execution
- Deterministic, reproducible pipelines
- Explicit human-in-the-loop (HITL) review
- Clear separation between core logic and adapters
- Evidence artifacts suitable for audit and traceability
- Minimal, defensible dependency surface

---

## Non-Goals

KProvEngine does **not** aim to be:

- A hosted service or SaaS
- An autonomous or agent-driven system
- A workflow orchestration framework
- A compliance-certified product

Claims of certification, regulatory approval, or automated validation are
intentionally avoided.

---

## High-Level Architecture






KProvEngine is structured as a **library-first core** with optional adapters:

- **Core pipeline**
  - Deterministic stages: normalize → parse → extract → render
  - No network access
  - No hidden state

- **Adapters**
  - Optional OCR and LLM integrations
  - Examples: EasyOCR, Tesseract, Ollama
  - Non-authoritative by design

- **Evidence layer**
  - Manifests and hashes
  - Provenance records
  - Toolchain disclosure
  - Explicit human review artifacts

See [`docs/architecture.md`](docs/architecture.md) for the authoritative diagram.

---

## Evidence Bundle (V1)

A typical run may produce:

- `run_summary.json`
- `manifest.json` — file paths and SHA-256 hashes
- `provenance.json` — execution metadata
- `toolchain.json` — tool and version disclosure
- `human_review.json` — explicit review status (PENDING allowed)

Artifacts support inspection and traceability.
They do **not** imply certification or validation.

---

## Quick Start (Local)

### Requirements

- Python **3.11 or 3.12**
- Virtual environment required (PEP 668 on macOS)
- swap python or alias python to python3 (on MacOS) if failure installing occurs.
-

### Setup

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"
```

### Run a demo

```bash
echo "Hello provenance" > input.txt
python -m kprovengine.cli input.txt --out runs
```

Inspect the generated `runs/<run-id>/` directory.

---

## Docker Demo (Optional)

```bash
docker build -t kprovengine:demo .
docker run --rm -v $(pwd):/work kprovengine:demo   python -m kprovengine.cli /work/input.txt --out /work/runs
```

Docker support is provided for experimentation and local isolation.
It is not required for V1 usage.

---

## Python Version Policy (V1)

Supported versions:

- Python 3.11
- Python 3.12

Python 3.13+ is intentionally excluded in V1 to ensure:

- Stable wheels
- Reproducible CI
- Consistent typing and tooling behavior
- Long-term support parity

Attempting to install KProvEngine with Python 3.13+ will fail by design.

---

## Governance & Scope Lock

V1 behavior is explicitly governed.

Authoritative documents:

- `docs/governance/PROMPT_V1_LOCKED.md`
- `docs/governance/REVIEW_GATE_V1.md`
- `docs/governance/STACK_V1_LOCKED.md`
- `docs/governance/CHANGE_CONTROL.md`

Changes outside V1 scope must be deferred to V2.

This is intentional.

---

## Status

This repository represents an early public V1 release.

The emphasis is on:

- Correctness
- Structure
- Security posture
- Governance discipline

Feature expansion is deferred until V2.

---

## License

MIT License. See `LICENSE`.

---

## Sponsorship

If this project is useful in professional or compliance-sensitive work,
consider sponsoring to support continued maintenance.
