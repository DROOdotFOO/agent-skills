#!/usr/bin/env python3
"""Validate the Codex packaging and host-neutral skill contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
MANIFEST_PATH = REPO_ROOT / ".codex-plugin" / "plugin.json"
PORTABILITY_EXEMPTIONS = {"claude-api"}


def load_skill_name(skill_md: Path) -> str | None:
    """Return the frontmatter name without requiring a YAML dependency."""
    match = re.search(r"^name:\s*([^\n]+)$", skill_md.read_text(), re.MULTILINE)
    return match.group(1).strip().strip('"\'') if match else None


def validate_manifest(errors: list[str]) -> None:
    """Check the Codex plugin entry point and its skills path."""
    if not MANIFEST_PATH.is_file():
        errors.append("missing .codex-plugin/plugin.json")
        return

    manifest = json.loads(MANIFEST_PATH.read_text())
    if manifest.get("name") != "agent-skills":
        errors.append("plugin name must be agent-skills")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
        errors.append("plugin version must use strict semver")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin skills path must be ./skills/")


def validate_skills(errors: list[str]) -> None:
    """Check unique names and reject unqualified host-specific instructions."""
    seen: dict[str, Path] = {}
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        folder_name = skill_md.parent.name
        skill_name = load_skill_name(skill_md)
        if skill_name != folder_name:
            errors.append(f"{skill_md}: frontmatter name must match directory")
            continue
        if skill_name in seen:
            errors.append(f"duplicate skill name {skill_name}: {seen[skill_name]} and {skill_md}")
        seen[skill_name] = skill_md

        if skill_name in PORTABILITY_EXEMPTIONS:
            continue

        text = skill_md.read_text()
        if re.search(r"`Agent` tool with `subagent_type`|Agent tool with `subagent_type`", text):
            errors.append(f"{skill_md}: hard-codes the Claude Agent tool")
        if re.search(r"\bsonnet subagents?\b", text, re.IGNORECASE):
            errors.append(f"{skill_md}: hard-codes a Claude model for delegation")
        if ("CLAUDE.md" in text or ".claude/" in text) and not (
            "AGENTS.md" in text or ".codex/" in text
        ):
            errors.append(f"{skill_md}: mentions Claude persistence without a Codex branch")


def main() -> None:
    """Run all Codex compatibility checks."""
    errors: list[str] = []
    if not (REPO_ROOT / "AGENTS.md").is_file():
        errors.append("missing repository AGENTS.md")

    validate_manifest(errors)
    validate_skills(errors)

    if errors:
        print("Codex compatibility failures:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Codex compatibility checks passed")


if __name__ == "__main__":
    main()
