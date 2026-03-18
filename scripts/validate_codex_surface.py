#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
FINDINGS = ROOT / "docs" / "FINDINGS_CODEX.md"
PROMPTS = ROOT / ".agents" / "PROMPTS.md"
SKILLS_DIR = ROOT / ".agents" / "skills"

REQUIRED_AGENTS_SECTIONS = (
    "Purpose",
    "Working mode",
    "Non-negotiables",
    "Technical requirements",
    "Repo operating guidance",
    "Required verification before finishing",
    "Deliverable format",
    "Guardrails",
)

REQUIRED_SKILL_SECTIONS = (
    "Why it exists",
    "When it should be invoked",
    "Expected inputs",
    "Expected outputs",
    "Constraints",
    "Verification expectations",
)

REQUIRED_PROMPT_SECTIONS = (
    "Audit only",
    "Audit + implementation",
    "Review only",
    "Release-readiness / verification",
    "Repo hygiene / instruction-surface review",
)


def _fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _has_heading(text: str, level: int, heading: str) -> bool:
    pattern = rf"(?m)^{'#' * level} {re.escape(heading)}\s*$"
    return re.search(pattern, text) is not None


def _parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = _read(path)
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML frontmatter fence")

    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing closing YAML frontmatter fence")

    frontmatter_block = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}

    for raw_line in frontmatter_block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {raw_line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")

    return data, body


def validate_agents() -> int:
    if not AGENTS.exists():
        return _fail("AGENTS.md is missing")

    text = _read(AGENTS)
    failures = 0

    for section in REQUIRED_AGENTS_SECTIONS:
        if not _has_heading(text, 2, section):
            failures += _fail(f"AGENTS.md missing required section: {section}")

    if "docs/FINDINGS_CODEX.md" not in text:
        failures += _fail("AGENTS.md should reference docs/FINDINGS_CODEX.md")

    if ".agents/" not in text:
        failures += _fail("AGENTS.md should reference the .agents instruction surface")

    return failures


def validate_findings() -> int:
    if not FINDINGS.exists():
        return _fail("docs/FINDINGS_CODEX.md is missing")
    return 0


def validate_prompts() -> int:
    if not PROMPTS.exists():
        return _fail(".agents/PROMPTS.md is missing")

    text = _read(PROMPTS)
    failures = 0

    for section in REQUIRED_PROMPT_SECTIONS:
        if not _has_heading(text, 2, section):
            failures += _fail(f".agents/PROMPTS.md missing required section: {section}")

    return failures


def validate_skills() -> int:
    if not SKILLS_DIR.exists():
        return _fail(".agents/skills is missing")

    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        return _fail("no repo-local skills found under .agents/skills")

    failures = 0
    names: list[str] = []

    for skill_file in skill_files:
        try:
            frontmatter, body = _parse_frontmatter(skill_file)
        except ValueError as exc:
            failures += _fail(f"{skill_file.relative_to(ROOT)}: {exc}")
            continue

        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")

        if not name:
            failures += _fail(f"{skill_file.relative_to(ROOT)}: missing frontmatter field 'name'")
        else:
            names.append(name)

        if not description:
            failures += _fail(
                f"{skill_file.relative_to(ROOT)}: missing frontmatter field 'description'"
            )

        for section in REQUIRED_SKILL_SECTIONS:
            if not _has_heading(body, 2, section):
                failures += _fail(
                    f"{skill_file.relative_to(ROOT)}: missing required section '{section}'"
                )

    duplicates = [name for name, count in Counter(names).items() if count > 1]
    for name in duplicates:
        failures += _fail(f"duplicate skill name detected: {name}")

    return failures


def main() -> int:
    failures = 0
    failures += validate_agents()
    failures += validate_findings()
    failures += validate_prompts()
    failures += validate_skills()

    if failures:
        return 1

    print("OK: Codex surface validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
