
# KProvEngine — Development Workflow (V1)

Status: Active
Applies to: KProvEngine v1.x
Audience: Maintainer / Reviewer

---

## Purpose

This document defines the **mandatory workflow** for developing, reviewing,
and committing changes to KProvEngine V1.

Its purpose is to:
- prevent scope drift
- prevent over-claiming functionality
- ensure architectural discipline
- maintain CI- and review-safe commits suitable for public visibility

This workflow is a **process control**, not a coding guide.

---

## Governing Documents (Authoritative)

All work must comply with:

1. `PROMPT_V1_LOCKED.md` — generation constraints
2. `REVIEW_GATE_V1.md` — verification and acceptance criteria
3. `STACK_V1_LOCKED.md` — allowed tools and dependencies
4. `CHANGE_CONTROL.md` — scope and version control

If a conflict exists, governance documents override convenience.

---

## Standard Development Cycle (Mandatory)

### 1. Define a Bounded Change Intent

Before generating or writing code, define the change in one short block:

- **Goal**: what is being added or modified
- **Non-goals**: what is explicitly excluded
- **Files**: expected files to change
- **Acceptance**: commands that must pass

Example:

Goal: add per-run output directory creation in pipeline scaffold
Non-goals: OCR, LLM usage, evidence bundle generation
Files: src/kprovengine/pipeline/run.py, tests/test_smoke.py
Acceptance: ruff check ., pytest -q, python -m build

If this cannot be written clearly, the change is not ready.

---

### 2. Generate Code as a Diff or Drop-in

When using an LLM for assistance:

- Request **unified diffs** for existing files
- Request **full drop-in files** only for new modules
- Do not mix narrative with code output

All generated code must remain import-safe and local-first.

---

### 3. Apply Changes and Run Local Gates Immediately

After applying changes, run **all gates locally**:

```bash
python -m ruff check .
python -m pytest -q
python -m build
```

Failures must be addressed before proceeding.

Do not “fix forward” with speculative changes.
Bring exact errors back for review if needed.

### 4. Run the Review Gate (Required)

Before committing, explicitly apply the review latch:

“Review this change against PROMPT_V1_LOCKED.md and REVIEW_GATE_V1.md.”

This review must confirm:
	•	Scope remains within V1
	•	No implied or explicit over-claims
	•	Core / adapter / evidence boundaries remain intact
	•	No hidden network access or nondeterministic side effects
	•	CI parity is preserved

If any answer is unclear, the change must be revised or deferred.

⸻

### 5. Commit with Intentional Boundaries

Each commit must:
	•	address one coherent change
	•	map directly to the Change Intent
	•	use a conventional, human-written message

Approved prefixes:
	•	feat: new surface area (including scaffolds)
	•	fix: correctness or stability
	•	docs: documentation only
	•	ci: CI or tooling
	•	security: security posture
	•	style: formatting or lint-only changes
	•	chore: maintenance without behavior change

Avoid:
	•	“WIP”
	•	multi-topic commits
	•	speculative or future-facing code

⸻

#### 6. Push Only After Local Parity Is Proven

Push changes only after all local gates pass.

After pushing:
	•	monitor CI workflows
	•	treat failures as incidents with root cause and minimal fixes

⸻

#### 7. Record Drift Pressure in BACKLOG.md

Any idea that:
	•	expands scope
	•	introduces new behavior
	•	depends on future tooling

must be recorded in BACKLOG.md, not implemented.

This includes:
	•	agents
	•	orchestration
	•	compliance automation
	•	hosted services
	•	performance optimizations

⸻

# Canonical LLM Usage Prompt (Verbatim)

Use this prompt when requesting code generation:


Role: Principal Engineer & Release Manager
Context: KProvEngine V1 (locked)
Task: <single bounded change>
Constraints: follow PROMPT_V1_LOCKED.md and REVIEW_GATE_V1.md; no scope expansion; local-first; no agents; no web services
I/O: unified diff or full drop-in files; include verification commands
Eval: ruff + pytest + build must pass
Safety: no secrets; no PII; no network calls
Style: Python 3.11, ruff-clean, import-safe


⸻

## Enforcement

Failure to follow this workflow invalidates the change.

Discipline is intentional.
Correctness and clarity take precedence over speed.
