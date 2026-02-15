OSS_GOVERNANCE.md

Purpose

This document defines the architectural, operational, and epistemic governance standards for the KProvEngine open-source core repository.

It exists to prevent architectural drift, hidden risk, dependency sprawl, behavioral regressions, and unverifiable changes.

All contributions must adhere to this contract.

⸻

1. Epistemic Discipline

All technical decisions, design proposals, and production-impacting changes must explicitly separate:
• FACT — Directly verifiable from source code or documentation.
• INFERENCE — Logical deduction from facts.
• ASSUMPTION — Requires confirmation; not verified.
• UNCERTAINTY — Unknown or insufficient context.
• CLAIM — Proposed action or design change.

If required context is missing, the process must halt until facts are obtained.

No guessing in production-facing code.

⸻

2. Change Classification

Every change must declare its risk level:
• SAFE — Non-behavioral change (formatting, comments, docs).
• LOW RISK — Localized logic change without interface impact.
• MEDIUM RISK — Behavior change without public interface change.
• HIGH RISK — Public interface change or architectural modification.

High-risk changes require explicit justification in PR description.

⸻

3. Public Interface Protection

The following are considered public interfaces:
• CLI flags and argument names
• CLI exit codes
• JSON output schema
• Directory layout guarantees
• Python package entrypoints

Rules:
• No breaking change without version bump.
• No silent modification of JSON schema.
• No silent change of exit codes.
• Backward compatibility must be stated.

⸻

4. Dependency Discipline

Runtime dependencies are attack surface.

Rules:
• No new runtime dependency without justification.
• Standard library preferred where feasible.
• Dev dependencies must not leak into runtime.
• Any dependency addition must state:
• Why stdlib is insufficient
• Security impact
• Maintenance impact

⸻

5. Determinism Requirement

All CLI and pipeline behavior must be deterministic.
• Exit codes must be stable.
• JSON output must be sorted and schema-consistent.
• Errors must be prefixed with error: and sent to stderr.
• Tests must verify CLI behavior via subprocess invocation.

⸻

6. Separation of Concerns

The repository enforces strict boundaries:
• pipeline/ contains business logic.
• cli.py contains argument parsing and process boundary only.
• CLI must not embed pipeline logic.
• No cross-layer side effects.

⸻

7. Testing Requirements

For any behavioral change:
• Subprocess CLI test must exist.
• Exit codes must be asserted.
• JSON schema must be asserted.
• Error paths must be tested.

Test files must not rely on global environment state.

⸻

8. Artifact Hygiene

The following must never be tracked:
• runtime runs/
• dist/
• coverage files
• demo outputs
• editor-specific files

Automated script scripts/check_tracked_artifacts.sh enforces this.

⸻

9. Branch Hygiene
   • One logical concern per commit.
   • No mixed refactor + feature in same commit.
   • Commit messages must follow:

    type(scope): concise summary
    Examples:
    • chore(oss): repo hygiene and artifact enforcement
    • feat(cli): deterministic exit codes
    • refactor(pipeline): isolate rendering stage

⸻

10. Release Discipline

Before tagging a release:
• All tests pass
• No unstaged changes
• CLI help output verified
• JSON contract verified
• Dependency list audited

⸻

11. Production Integrity Rule

If a recommendation cannot clearly satisfy:
• Epistemic separation
• Risk classification
• Determinism
• Backward compatibility

It is not acceptable for this repository.

⸻

12. Open Source vs Enterprise Boundary

This repository represents the OSS core.

Enterprise-specific features must not:
• Modify core behavior
• Introduce hidden runtime hooks
• Add conditional logic based on environment

Enterprise logic must exist in a separate repository or adapter layer.

⸻

13. Decision Gate Protocol

When evaluating architectural changes: 1. Gather facts from code. 2. Identify uncertainty. 3. Halt if unknowns exist. 4. Propose minimal viable change. 5. Classify risk. 6. Provide verification commands.

No speculative refactoring.

⸻

14. Trust Standard

If these governance rules are not followed in a proposal or change:

The recommendation is not safe for production or public OSS use.

⸻

End of Governance Contract.
