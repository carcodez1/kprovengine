---
name: instruction-surface-maintenance
description: Maintain the repo-local Codex operating surface for kprovengine. Use when changing AGENTS.md, .agents/skills, reusable prompts, docs/FINDINGS_CODEX.md, or validation hooks that govern how Codex should work in this repository.
---

# Instruction Surface Maintenance

## Why it exists

The repository now has a dedicated Codex operating layer. It needs to stay durable, narrow, enforceable, and aligned with the real repository rather than becoming another stale documentation pile.

## When it should be invoked

- `AGENTS.md` changes
- `.agents/**` changes
- prompt-template changes
- Codex-surface validation or pre-commit hook changes
- requests to create, split, merge, or retire repo-local skills

## Expected inputs

- requested instruction-surface change
- touched files or desired skill additions
- reason the new guidance or skill is needed

## Expected outputs

- audit of the current instruction surface
- file plan with minimal justified additions
- updated skills or prompts with clear routing boundaries
- validation commands and any remaining overlap risks

## Constraints

- Keep `AGENTS.md` repo-wide and durable.
- Keep skills narrow, reusable, and non-overlapping.
- Do not restate the entire governance set inside skills.
- Add scripts only when they provide deterministic repeated value.
- Avoid hardcoded model IDs or brittle vendor-specific instructions.

## Workflow

1. Audit the current instruction surface before patching.
2. Identify the highest-ROI recurring workflows in the repo.
3. Create only the justified skills and make their triggers specific.
4. Add or update deterministic validation if the surface becomes harder to review manually.
5. Run the Codex-surface validator and ensure hooks or docs point to the new source of truth.

## Verification expectations

- Run `python3 scripts/validate_codex_surface.py`.
- If `.pre-commit-config.yaml` changed, run the relevant local pre-commit path if available.
- Confirm each skill has valid frontmatter and the required body sections.
