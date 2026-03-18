---
name: governance-review
description: Review kprovengine changes against the locked V1 governance set, public claim boundaries, CI gates, and contract-affecting documentation. Use when touching docs/governance, README claims, public behavior, workflows, or compliance/security language.
---

# Governance Review

## Why it exists

This repository is governance-heavy. Changes can be technically small but still violate V1 scope, public-claim boundaries, or documented release controls.

## When it should be invoked

- `docs/governance/**`, `README.md`, `SECURITY.md`, or `OSS_GOVERNANCE.md` changes
- CI/workflow changes that alter required checks or release posture
- CLI or artifact contract changes
- requests for audits, reviews, release-readiness, or compliance/security positioning

## Expected inputs

- change intent
- touched files or diff
- requested output mode: audit only, review only, or audit plus implementation

## Expected outputs

- findings ordered by severity with file references
- explicit scope and claim-drift assessment
- verification commands tied to the changed surface
- residual risks and open questions

## Constraints

- Treat `docs/governance/PROMPT_V1_LOCKED.md`, `REVIEW_GATE_V1.md`, `CHANGE_CONTROL.md`, and `STACK_V1_LOCKED.md` as authoritative.
- Do not endorse compliance or certification claims the repo cannot verify.
- Flag documentation-to-code drift explicitly.
- Keep recommendations bounded to the actual changed surface.

## Workflow

1. Read the change intent and touched files.
2. Load only the governance docs needed for the touched surface.
3. Check for:
   - scope expansion beyond V1
   - implied functionality not implemented
   - claim drift in docs, workflows, or outputs
   - CI/local parity regressions
   - locked-file edits or changes that should be deferred
4. Cross-check docs against code and tests when a public contract is described.
5. Report findings first. If there are no findings, state that explicitly and list remaining risks.

## Verification expectations

- Run targeted local verification for the changed surface.
- Use `make preflight` when the environment supports the full gate set.
- At minimum, state which of `ruff`, `pytest`, `build`, and script/workflow checks were run or not run.
