# Contributing to KProvEngine (OSS Core)

## 1. Scope

This repository contains the **public OSS core (V1)** of KProvEngine.

It provides:

- Deterministic CLI behavior
- Stable JSON output contracts
- Reproducible artifact layout
- No cloud dependencies
- No enterprise control logic

Enterprise extensions are out of scope.

---

## 2. Governance Model

Maintainer-led model.

- Repository owner has final merge authority.
- Breaking changes require prior issue discussion.
- Public interfaces are contract-locked (see OSS_GOVERNANCE.md).

---

## 3. Public Contract Surfaces (V1 LOCKED)

The following are considered stable public interfaces:

- CLI flags and exit codes
- JSON output schema (see `/schemas`)
- Package entrypoints
- Artifact directory structure

Breaking changes require:

1. Major version bump
2. Schema update
3. Test update
4. Governance documentation update

No exceptions.

---

## 4. Development Workflow

### 4.1 Branching

- `main` is protected.
- Work must occur in feature or chore branches.
- Pull requests required.

### 4.2 Required Gates

Before submitting a PR:
make preflight
tox

This enforces:

- Ruff lint
- Pytest
- sdist + wheel build
- Artifact hygiene
- Identity guard
- SBOM generation
- Pre-commit hooks

PRs failing gates will not be merged.

---

## 5. Dependency Policy

Runtime dependencies are strongly discouraged.

Adding a runtime dependency requires:

- Justification in PR
- Security impact statement
- Maintenance assessment

Dev/test dependencies allowed.

---

## 6. Security

See `SECURITY.md`.

Do not disclose vulnerabilities publicly before coordinated response.

---

## 7. Commit Standards

Use conventional commit prefixes:

- `feat:`
- `fix:`
- `chore:`
- `docs:`
- `test:`
- `refactor:`

All commits must:

- Pass CI
- Not introduce tracked artifacts
- Preserve identity constraints

---

## 8. Artifact Hygiene

The following must never be committed:

- runs/
- demo_runs/
- dist/
- coverage artifacts
- compiled bytecode

Enforced via:
scripts/check_tracked_artifacts.sh

---

## 9. Schema Discipline

All JSON artifacts must conform to schemas in `/schemas`.

Any change to JSON output requires:

- Schema update
- Test update
- Version impact discussion

---

## 10. License

MIT License applies to OSS core only.

Enterprise modules are not included in this repository.

---

By contributing, you agree that your contributions are licensed under the MIT License.
