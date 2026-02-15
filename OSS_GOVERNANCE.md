# Open Source Governance — KProvEngine (Public Core)

## 1. Purpose and Scope

This document defines the public governance policy for the
KProvEngine open-source core.

KProvEngine is a **local-first provenance engine** for
deterministic, reproducible, and auditable human + AI workflows.

This core repository (V1) provides:

- Python library APIs
- A CLI with deterministic exit codes and stable JSON output
- No cloud dependencies
- No implicit external services

This governance applies to the public OSS core only. Enterprise
extensions and private adaptations are outside this scope.

## 2. Versioning Policy

KProvEngine follows **Semantic Versioning (SemVer)**.

- Version numbers are `MAJOR.MINOR.PATCH`.
- Minor releases add functionality in a backward-compatible way.
- Patch releases fix bugs without changing public behavior.
- Breaking changes require a major version bump and clear
  migration guidance.

## 3. Public Interface Stability

The following are considered public interfaces:

- CLI commands, flags, and exit codes
- JSON output schemas
- Python module import paths and public classes/functions
- Package entrypoints

These must not be changed without:

1. Explicit rationale in PR description.
2. Test coverage asserting behavior.
3. Versioning bump according to SemVer.

## 4. Determinism & Contract Guarantees

KProvEngine guarantees:

- Deterministic exit codes for CLI runs.
- JSON output ordering and key stability when `--format=json`.
- CLI errors prefixed with `"error:"` and written to stderr.

Contributors must add tests for invariants where behavior
could vary.

## 5. Change Control

All public code changes must satisfy:

1. **Automated Gates**
    - Lint (ruff) passes
    - Tests (pytest) pass
    - Build (sdist + wheel) succeeds

2. **Code Review Discipline**
    - PRs must include description of impact surface
    - Backward compatibility must be discussed
    - Test cases for affected behavior must be included

3. **Dependency Review**
    - No new **runtime** dependency without explicit justification
    - Only dev/test dependencies may be introduced as needed
    - Long-term maintenance and security impact must be stated

## 6. Security Reporting

Security issues must be reported privately via: plewak.jeff@gmail.com.

Public disclosure without prior coordination is discouraged until
a patch is available.

SECURITY.md describes the disclosure process.

## 7. Contribution Process

See **CONTRIBUTING.md** for:

- Branching model
- PR templates
- Issue triage
- Code ownership

Minimum requirements:

- A descriptive title + summary
- Link to relevant tests
- Clear rationale for change
- Version impact statement

## 8. Artifact Hygiene

The following must not be tracked in the repository:

runs/
demo_runs/
dist/
\*.egg-info/
.coverage
coverage.xml
htmlcov/

Use `scripts/check_tracked_artifacts.sh` to enforce this.

## 9. CI and Merge Requirements

On GitHub:

- Protect the `main` branch.
- Required status checks:
  • The ci workflow must pass for all supported Python versions (matrix).
  • If additional enforcement workflows exist (e.g., security, docker-ci), they must also pass when present.

Drafts and WIP commits are not protected.

## 10. Governance Model

This repository uses a **Maintainer-Lead model**.

- The repository owner has final merge authority.
- Trusted contributors are granted maintainer rights.
- Any high-risk change (interface, major version) must be
  discussed in an issue before work.

---

## Summary of Public Guarantees

| Guarantee                         | Required |
| --------------------------------- | -------- |
| Deterministic CLI behavior        | Yes      |
| Semantic Versioning               | Yes      |
| Test coverage for behavior        | Yes      |
| No runtime deps without reason    | Yes      |
| Backward compatibility protection | Yes      |
| Security process described        | Yes      |

Thank you for contributing to the stability and credibility of
KProvEngine.

---
