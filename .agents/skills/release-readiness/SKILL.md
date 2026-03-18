---
name: release-readiness
description: Review or refine kprovengine's release, CI, SBOM, signing, attestation, and supply-chain verification surfaces. Use when touching .github/workflows, Dockerfile, Makefile, or scripts such as sbom.sh, sign.sh, attest.sh, release.sh, and related docs.
---

# Release Readiness

## Why it exists

This repository has a real release-evidence stack: build, SBOM, signing, attestation, artifact hygiene, and identity checks. Those surfaces are easy to drift independently unless reviewed as one system.

## When it should be invoked

- `.github/workflows/**` changes
- `Dockerfile`, `Makefile`, or release/supply-chain script changes
- release-readiness or CI-parity audits
- questions about SBOM, signing, attestation, or artifact verification posture

## Expected inputs

- touched files or diff
- intended release path: local, CI, tag release, or audit only
- any known environment constraints such as missing `syft` or `cosign`

## Expected outputs

- findings on release-surface correctness and parity
- required verification commands
- blockers for release readiness
- minimal follow-up changes if the surface is incomplete

## Constraints

- Keep recommendations tied to the existing local-first OSS core.
- Do not invent compliance status or SLSA levels the repo cannot prove.
- Distinguish between release-time evidence and runtime evidence.
- Avoid broad workflow rewrites when a narrow fix will do.

## Workflow

1. Read the affected workflow, script, and helper commands together.
2. Cross-check local and CI parity:
   - `Makefile`
   - release/security workflows
   - relevant scripts in `scripts/`
3. Check artifact completeness:
   - build outputs
   - SBOM outputs
   - signature bundles
   - attestation verification steps
4. Identify duplicate, stale, or conflicting workflow paths.
5. Report findings first or patch the smallest parity fix.

## Verification expectations

- Run targeted commands for the changed surface.
- Use `python -m build -q` for packaging changes.
- Use `python -m pre_commit run --all-files` or the relevant local hook path when workflow or validation surfaces changed.
- State clearly if `syft`, `cosign`, or tag-triggered workflows were not exercised locally.
