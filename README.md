# KProvEngine
[![CI](https://github.com/carcodez1/KProvEngine/actions/workflows/ci.yml/badge.svg)](https://github.com/carcodez1/KProvEngine/actions/workflows/ci.yml)
[![Security](https://github.com/carcodez1/KProvEngine/actions/workflows/security.yml/badge.svg)](https://github.com/carcodez1/KProvEngine/actions/workflows/security.yml)
![Python](https://img.shields.io/badge/python-3.11–3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Scope](https://img.shields.io/badge/scope-V1%20locked-critical)

KProvEngine is a **local-first provenance engine** for AI-assisted human workflows.
It converts unstructured artifacts into structured outputs while producing
verifiable evidence of execution, authorship, and human review.

The project is intentionally conservative. AI may assist extraction and
structuring, but **humans remain the authority**.

This repository prioritizes correctness, traceability, and governance over
feature breadth.

---

## Design Goals

- Local-first execution by default
- Deterministic, reproducible pipelines
- Clear separation between core logic and adapters
- Explicit human-in-the-loop (HITL) review
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

KProvEngine is structured as a **library-first core** with thin adapters:

- **Core pipeline**
  - Deterministic stages: normalize → parse → extract → render
  - No network access or hidden state
- **Adapters**
  - Swappable OCR and LLM integrations
  - Examples: EasyOCR, Tesseract, Ollama
  - Optional and non-authoritative by design
- **Evidence layer**
  - Manifests, hashes, provenance records
  - Explicit human review and attestation artifacts

This separation allows AI tooling to evolve without compromising provenance or
audit guarantees.

---

## Evidence Bundle (V1)

A typical run may produce an evidence directory containing:

- `manifest.json` — file paths and SHA-256 hashes
- `provenance.json` — execution metadata
- `toolchain.json` — tool and version disclosure
- `human_review.json` — explicit review status (PENDING allowed)
- `hashes.txt` — content hashes
- `attestation.md` — human-authored statement
- `sbom.json` — software bill of materials (CI-generated when available)

Artifacts support inspection and traceability; they do **not** imply
certification or validation.

## Architecture

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the authoritative Mermaid source.

![KProvEngine V1 architecture](docs/images/architecture.png)

The design emphasizes deterministic execution, optional AI assistance,
and explicit human review.

## Status

This repository represents an **early public V1 release** with scope explicitly
locked.

V1 emphasizes governance and structure first to prevent invalid claims as
functionality is added.

The focus is on:
- correctness
- structure
- security posture
- governance discipline

Feature expansion is deferred until V2.

Authoritative constraints and review rules live in `docs/governance/`.

---

## Python Version Policy (V1)

**Supported Python versions:** **3.11–3.12**

V1 intentionally excludes Python 3.13+ (including 3.14) to ensure:
- stable wheels
- reproducible CI
- consistent typing and tooling behavior
- long-term support parity across environments

Attempting to install KProvEngine with Python 3.13+ will fail by design.

---

## Virtual Environments & PEP 668 (Important)

On macOS, Homebrew Python is **externally managed** (PEP 668).
Do **not** install packages system-wide.

Always use a virtual environment.

### Recommended Setup (macOS / Homebrew)

```bash
brew install python@3.12

rm -rf .venv
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
source .venv/bin/activate

python -V        # should show 3.12.x
python -m pip install -U pip
python -m pip install -e ".[dev]"
>>>>>>> Stashed changes
