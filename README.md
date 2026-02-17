# kprovengine

## Status

![CI](https://github.com/carcodez1/kprovengine/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)

Supported Python: `>=3.11,<3.13`
Deterministic provenance and governance scaffolding for evidence-ready pipelines.

kprovengine V1 is a governance-locked open-source core focused on deterministic execution, runtime policy enforcement, artifact hygiene, and identity surface control.

---

## Table of Contents

- [Status](#status)
- [Overview](#overview)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [End-to-End Use Case](#end-to-end-use-case)
- [Installation](#installation)
- [Example Execution](#example-execution)
- [Development Workflow](#development-workflow)
- [Governance Model](#governance-model)
- [Versioning Contract](#versioning-contract)
- [Scope Boundaries (V1)](#scope-boundaries-v1)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

Most modern data, ML, and compliance pipelines fail in governance, not logic.

Common failure modes:

- Runtime drift across environments
- Undetected artifact pollution
- Identity inconsistencies
- Incomplete traceability surfaces
- CI that does not mirror local enforcement
- Governance rules enforced socially instead of technically

kprovengine V1 establishes:

- Deterministic CLI execution
- Runtime Python version enforcement
- Canonical repository identity enforcement
- Artifact boundary control
- Cross-version CI test matrix
- Fail-closed governance surfaces

This is infrastructure, not a demo framework.

---

## Core Capabilities

### 1. Identity Guard

- Technical identity enforcement (kprovengine)
- Controlled display identity surface
- Forbidden token scanning
- Canonical repository URL verification
- Docker label validation

### 2. Artifact Guard

- Fails if runtime artifacts are tracked
- Enforces clean repository boundaries
- Protects release integrity

### 3. Python Version Policy

- Enforced `>=3.11,<3.13`
- Validated locally and in CI
- Fail-closed enforcement

#

unset -f pip python 2>/dev/null || true
unalias pip python 2>/dev/null || true
export VIRTUAL_ENV="$PWD/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"
hash -r
python -V
pip -V
pip install -e ".[dev]"

./.venv/bin/python -m pip ...

make preflight

### 4. CI Parity

Local:

```
make preflight
```

CI:

- lint (ruff)
- test (3.11 / 3.12)
- build
- artifact guard
- identity guard
- pre-commit
- python policy enforcement

If local preflight passes, CI should pass.

---

## Architecture

### Execution Flow

```
User Input
   │
   ▼
CLI (argparse)
   │
   ▼
Deterministic Processing Core
   │
   ├── run_summary.json
   ├── provenance.json
   ├── toolchain.json
   └── human_review.json
   │
   ▼
Filesystem Output (timestamp-scoped)
```

Each run produces structured evidence artifacts.

All outputs are:

- Deterministic
- Version-traceable
- Runtime-policy validated
- Governed by identity enforcement

---

## End-to-End Use Case

### Scenario: Compliance-Aware Data Transformation

A regulated team processes input artifacts that must:

- Be reproducible
- Record toolchain state
- Preserve provenance metadata
- Prevent identity spoofing
- Maintain runtime version traceability

Execution:

```
python -m kprovengine.cli input.txt --out runs/
```

Output:

```
runs/2026-02-15T20-13-00Z/
  run_summary.json
  provenance.json
  toolchain.json
  human_review.json
```

What this guarantees:

- Exact runtime Python version captured
- Deterministic artifact generation
- Toolchain snapshot
- Human review placeholder contract
- Governance compliance gates enforced before merge

This provides a compliance-ready execution scaffold, not just transformation logic.

---

## Installation

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

---

## Example Execution

```
python -m kprovengine.cli input.txt --out runs/
```

---

## Development Workflow

```
make preflight
```

This runs:

- lint
- test
- build
- artifact guard
- identity guard
- pre-commit

Preflight is deterministic and mirrors CI.

---

## Governance Model

Governance is codified, not implied.

Enforced contracts:

- Canonical repository surface validation
- Display name scope restrictions
- Forbidden identity token detection
- Python runtime policy enforcement
- Artifact hygiene guard
- Required CI checks before merge

Governance logic lives in:

```
docs/governance/
scripts/check_project_identity.py
scripts/check_tracked_artifacts.sh
scripts/check_venv_python.py
```

Changes to governance logic require version elevation.

---

## Versioning Contract

V1 is governance-locked.

Breaking changes include:

- Runtime policy modifications
- Identity enforcement surface changes
- Artifact guard rule changes
- CI enforcement changes

Such changes require major version increment.

---

## Scope Boundaries (V1)

Excluded intentionally:

- Enterprise compliance adapters
- Policy-as-code engines
- Signed artifact infrastructure
- External audit integrations
- SaaS multi-tenant features

V1 is the deterministic OSS governance core.

---

## Roadmap

Future versions may introduce:

- Evidence bundle export schemas
- Signed artifact pipelines
- Compliance framework adapters (NIST / ISO)
- Enterprise integration layers

These are intentionally excluded from V1.

---

## License

MIT License
© 2026 Jeffrey Plewak

See LICENSE for details.
