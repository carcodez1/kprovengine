---
name: evidence-contract-audit
description: Review or change the artifact-contract surface for kprovengine runs, including CLI output, evidence files, manifest/provenance/toolchain behavior, traceability docs, and related tests. Use when touching src/kprovengine/evidence, manifest, pipeline, storage, tests/schemas, or CLI contract tests.
---

# Evidence Contract Audit

## Why it exists

The repository's value depends on stable evidence artifacts and contract traceability. Small code changes in the pipeline, CLI, or docs can silently break those guarantees.

## When it should be invoked

- changes under `src/kprovengine/evidence/`
- changes under `src/kprovengine/manifest/`
- changes to `src/kprovengine/pipeline/run.py`, `src/kprovengine/cli.py`, or `src/kprovengine/storage/layout.py`
- changes to `tests/schemas/` or contract-oriented tests
- requests to explain, review, or extend emitted evidence artifacts

## Expected inputs

- change intent and expected artifact impact
- touched files or diff
- current artifact expectations, if the task mentions them

## Expected outputs

- artifact-level impact summary
- findings on code/schema/test/doc alignment
- exact verification commands for the affected contract
- risks of backward-incompatible drift

## Constraints

- Keep artifact changes deterministic and local-first.
- Do not add evidence files or fields without updating tests and traceability docs.
- Treat missing implementation versus documented guarantees as a finding, not a footnote.
- Do not broaden the task into general product work.

## Workflow

1. Read the contract-defining code and the matching tests.
2. Load traceability docs only as needed:
   - `docs/governance/TOOLCHAIN_SCHEMA_V1.md`
   - `docs/governance/v1_SCHEMA_TRACEABILITY.md`
3. Compare:
   - emitted artifacts
   - documented artifacts
   - test-enforced artifacts
4. Identify contract drift, missing coverage, or inconsistent naming.
5. If patching, update the smallest set of code, docs, and tests needed to restore alignment.

## Verification expectations

- Run targeted `pytest` coverage for the affected contract tests.
- Run `python -m ruff check .` if code changed.
- Run `python -m build -q` if packaging or public CLI contract surfaces changed.
