# AGENTS.md

## Purpose

This repository is the public `kprovengine` OSS core: a local-first Python package and CLI for deterministic provenance, evidence artifacts, and supply-chain-aware release workflows.

This file defines the repo-local Codex operating system for day-to-day work. It should stay durable, repo-wide, and implementation-focused. It must not restate the locked V1 governance documents line-by-line.

Authoritative references:

- `docs/governance/PROMPT_V1_LOCKED.md`
- `docs/governance/REVIEW_GATE_V1.md`
- `docs/governance/CHANGE_CONTROL.md`
- `docs/governance/STACK_V1_LOCKED.md`
- `docs/FINDINGS_CODEX.md`

## Working mode

- Inspect the repository first. Do not infer architecture, workflows, or contracts without reading the relevant files.
- Define a bounded change intent before patching: goal, non-goals, files, and verification.
- Prefer diff-first, surgical changes over rewrites.
- Keep changes local-first, deterministic, and reviewable.
- For review tasks, lead with findings ordered by severity and tied to file references.
- Treat existing user changes in the worktree as authoritative unless they directly block the requested task.

## Non-negotiables

- No uncontrolled rewrites.
- No new runtime dependency without explicit signed approval.
- No changes to public contracts without matching tests and documentation.
- No hidden network access, background services, or agentic behavior.
- No PHI, secrets, keys, or sensitive logs in code, tests, docs, fixtures, or generated outputs.
- No compliance or certification claims beyond what the repository actually implements and verifies.
- No edits to locked governance documents unless the task explicitly authorizes that path and follows the repository's governance process.
- Policy-affecting prompts and all commits must follow the signing requirements in `docs/FINDINGS_CODEX.md`.

## Technical requirements

- Runtime: Python `>=3.11,<3.13`
- Package layout: `src/kprovengine`
- Tests: `pytest`
- Lint: `ruff`
- Matrix checks: `tox`
- Packaging: `python -m build`
- Release evidence: `scripts/sbom.sh`, `scripts/sign.sh`, `scripts/attest.sh`
- Local parity entrypoint: `make preflight`

Critical directories:

- `src/kprovengine/`: public library, CLI, pipeline, evidence, manifest, storage
- `tests/`: unit and integration contract coverage
- `scripts/`: deterministic validation, release, and hygiene helpers
- `.github/workflows/`: CI, security, release, Docker, and E2E surfaces
- `docs/governance/`: locked V1 governance and contract references
- `.agents/`: repo-local Codex skills and prompt templates

## Repo operating guidance

### Public surfaces

Treat the following as public or externally consumed unless the task says otherwise:

- package metadata in `pyproject.toml`
- CLI behavior and output contracts
- evidence artifact names and JSON surfaces
- build, release, SBOM, signing, and attestation workflows
- user-facing documentation in `README.md`, `docs/`, and release-facing scripts

### Private and admin surfaces

Treat the following as administrative control surfaces:

- `.agents/`
- `AGENTS.md`
- `docs/FINDINGS_CODEX.md`
- `.github/`
- `docs/governance/`
- local validation scripts for instruction surfaces

### Public Search / Semantic Indexing Policy

- Prefer repository inspection over external search.
- Use external research only when facts are unstable, high-stakes, or explicitly requested.
- For normative claims about regulation, compliance, security, provenance, or standards, use the source policy in `docs/FINDINGS_CODEX.md`.
- If an external source is not approved by repository policy, treat it as non-authoritative and label any resulting statement as inference.

### Skill routing guidance

Use the repo-local skills when their triggers match:

- `governance-review`: scope drift, public claims, governance docs, CI gates, or contract-affecting reviews
- `evidence-contract-audit`: artifact schemas, CLI output, pipeline evidence, manifest/provenance/toolchain alignment
- `release-readiness`: release workflows, supply-chain evidence, SBOM/signing/attestation, Docker or CI parity
- `instruction-surface-maintenance`: `AGENTS.md`, `.agents/`, reusable prompts, and Codex-surface validation

If more than one skill applies, use only the minimal set needed to cover the task.

### MCP / tool posture

- Prefer repo-local files, deterministic scripts, and primary sources over ad hoc reasoning.
- Prefer `rg`, `sed`, `pytest`, `ruff`, `tox`, `make`, and stdlib Python.
- Do not introduce network-dependent scripts or validation paths without explicit approval.
- Do not rely on brittle model IDs or vendor-specific prompting assumptions in repository guidance.

## Required verification before finishing

- If `AGENTS.md`, `.agents/`, `.pre-commit-config.yaml`, or Codex-surface validation scripts changed:
  - `python3 scripts/validate_codex_surface.py`
- If Python source or tests changed:
  - `python -m ruff check .`
  - `python -m pytest -q`
- If packaging or release surfaces changed:
  - `python -m build -q`
  - relevant targeted script checks for `sbom`, `sign`, `attest`, or workflow parity
- If the task is broad and prerequisites are present:
  - `make preflight`

Always state what you did not run and why.

## Deliverable format

Every substantial task should end with:

- bounded change intent
- `FACT / INFERENCE / ASSUMPTION / UNKNOWN`
- findings or file plan
- unified diffs or a concise file-linked change summary
- verification commands and results
- remaining risks, blockers, or follow-up items

For review-only tasks, findings come first.

## Guardrails

- Keep the smallest defensible scope.
- Prefer enhancement over replacement.
- Do not invent schemas, workflows, compliance mappings, or operating procedures not grounded in this repository.
- Keep adapters optional and non-authoritative.
- Preserve accessibility, determinism, and local-first behavior.
- Keep the instruction surface synchronized: `AGENTS.md`, `.agents/`, `docs/FINDINGS_CODEX.md`, and validation hooks should not drift silently.
- If the worktree is dirty in overlapping files, stop and reason carefully before patching.
