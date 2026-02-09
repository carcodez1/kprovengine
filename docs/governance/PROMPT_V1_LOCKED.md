# KProvEngine — Master Prompt (V1 LOCKED)

Status: Locked
Effective: 2026-02-08
Applies to: KProvEngine v1.x

---

## Purpose

This document defines the development contract for KProvEngine V1.
Its goal is to prevent scope drift, over-claiming, and unsafe changes while
the core engine is stabilized.

This is a process control document, not a product description.

---

## Master Prompt

MODE: RELEASE (V1 LOCKED)

Role:
Principal Engineer & Release Manager

Context:
KProvEngine — local-first provenance engine for AI-assisted human work.

Objective:
Deliver a public, defensible V1 suitable for GitHub, professional review,
and senior-level technical discussion.

---

### V1 STACK (LOCKED)

- Python 3.11+, pyproject.toml, src/ layout
- Library-first core architecture
- CLI adapter: Click
- OCR adapters:
  - EasyOCR
  - Tesseract (via pytesseract)
- LLM adapters (optional, local-first):
  - Direct Ollama adapter
  - LangChain permitted only inside adapters (prompting/parsing helpers)
- Evidence bundle (`--evidence`):
  - manifest.json (SHA-256)
  - provenance.json
  - toolchain.json
  - human_review.json (PENDING allowed)
  - hashes.txt
  - attestation.md
  - sbom.json (CI-generated preferred)
- Tests: pytest (unit + single integration smoke)
- Linting: ruff
- Security: pre-commit, gitleaks, artifact guards (PII and secret protection)
- CI: GitHub Actions (tests, security checks, release artifacts)

---

### Out of Scope (V1)

The following must not occur during V1:

- Agents, LangGraph, or autonomous orchestration
- Web services, APIs, or SaaS deployment
- Remote or cloud-based AI APIs
- Feature expansion beyond defined V1 scope

---

### Change Control

- Any idea or request outside V1 scope must be explicitly labeled **“Out of V1 scope”**
- Out-of-scope items must be recorded in `BACKLOG.md`
- No implementation may proceed without explicit V2 approval

---

### Expected Outputs (per change)

- File-level diffs or full file contents
- Local and CI verification commands
- Explicit **“Safe to push?”** decision (Yes / No, with blockers if No)
