# KProvEngine — Developer Card (V1)

Applies to: V1.x
Purpose: fast re-entry + drift prevention

## What you are building (V1)
Local-first provenance engine with:
- deterministic pipeline stages
- optional OCR/LLM adapters (non-authoritative)
- evidence bundle artifacts with explicit HITL

No agents. No SaaS. No compliance claims.

## Governance anchors (must not drift)
- PROMPT: docs/governance/PROMPT_V1_LOCKED.md
- STACK: docs/governance/STACK_V1_LOCKED.md
- CHANGE CONTROL: docs/governance/CHANGE_CONTROL.md
- REVIEW GATE: docs/governance/REVIEW_GATE_V1.md

## Daily workflow (do this)
1) Pull latest main and create a branch
2) Implement smallest defensible change
3) Run: `make preflight` (or `bash scripts/preflight.sh`)
4) Commit with a clear message
5) Open PR; keep scope narrow

## When you MUST update snapshots
If you edit anything in `docs/governance/`:
- add a new snapshot under `docs/snapshots/` (dated)
- link it from the governance change PR

## “Safe to merge” definition (V1)
- preflight passes locally
- CI green
- no new deps unless explicitly justified and aligned with STACK
- no scope/claim drift per REVIEW_GATE_V1.md

## Copy-paste PR footer
Reviewed against:
- PROMPT_V1_LOCKED.md
- REVIEW_GATE_V1.md
No scope, stack, or claim drift. CI green.
