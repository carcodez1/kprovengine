# Recommended Codex Prompts

Use these as starting points for recurring work in this repository. Replace bracketed values with task-specific details.

## Audit only

```text
Role: Principal reviewer for kprovengine
Task: Audit [files or area] only. Do not patch.
Use skills: governance-review [and/or evidence-contract-audit if applicable]
Focus: bugs, contract drift, governance drift, release risk, missing verification
Output: findings first, then assumptions, then targeted verification commands
Constraints: no speculative claims, no scope expansion, no patching
```

## Audit + implementation

```text
Role: Principal engineer for kprovengine
Task: Audit [files or area], then implement the smallest defensible fix.
Use skills: [governance-review / evidence-contract-audit / release-readiness as applicable]
Change intent:
- Goal: [goal]
- Non-goals: [non-goals]
- Files: [expected files]
- Acceptance: [commands]
Output: findings, file plan, unified diff, verification notes, remaining risks
Constraints: diff-first, surgical changes only, preserve V1 scope
```

## Review only

```text
Role: Senior code reviewer for kprovengine
Task: Review the staged or described change only.
Use skills: governance-review when the change affects public behavior, docs, CI, or governance
Focus: correctness, behavioral regressions, contract impact, missing tests, release risk
Output: findings ordered by severity with file references, then open questions, then residual risks
Constraints: do not summarize first; do not patch
```

## Release-readiness / verification

```text
Role: Release readiness reviewer for kprovengine
Task: Validate [release path, workflow, or script set] for local/CI parity and supply-chain evidence completeness.
Use skills: release-readiness
Check: build, SBOM generation, signing, attestation, artifact guard, identity guard, workflow duplication, verifier instructions
Output: findings, required verification commands, blockers, and smallest next fixes
Constraints: no new dependencies without approval, no invented compliance claims
```

## Repo hygiene / instruction-surface review

```text
Role: Codex workflow architect for kprovengine
Task: Review and refine the repo-local instruction surface only.
Use skills: instruction-surface-maintenance [and governance-review if public claims or governance docs are touched]
Focus: AGENTS.md durability, skill routing quality, overlap between skills, enforceability, prompt quality, validation coverage
Output: audit findings, file plan, unified diff, verification notes, follow-up items
Constraints: keep guidance repo-specific, durable, and minimal-blast-radius
```
