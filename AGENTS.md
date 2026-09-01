# AGENTS.md

## Repository purpose

This repository contains portable `SKILL.md` workflows and nine standalone
Python agent CLIs that also expose MCP servers. Raxol, Codex, and Claude Code
must consume the same skill instructions without host-specific assumptions.

## Required checks

- Run `./scripts/skills-lint.sh` after changing any skill.
- Run `python3 scripts/skill-triggers-test.py` after changing skill discovery text.
- Run `python3 scripts/codex-compat-test.py` after changing skills or plugin metadata.
- Run the affected agent's pytest suite after changing Python code.
- Keep shell scripts `set -euo pipefail` and shellcheck-clean.
- Keep Python typed and formatted with Ruff.

## Skill rules

- Every skill directory has a `SKILL.md` whose `name` matches the directory.
- Descriptions contain specific `TRIGGER when:` and `DO NOT TRIGGER` boundaries.
- Keep workflows capability-based. When hosts differ, document explicit Codex,
  Claude Code, and Raxol branches instead of assuming one tool name or config path.
- Supporting Markdown files retain their `impact`, `impactDescription`, and
  comma-separated `tags` frontmatter.
- Do not add empty modules, placeholder skills, or claims about unavailable tools.

## Distribution boundaries

- `.codex-plugin/plugin.json` is the Codex plugin entry point.
- `.claude-plugin/` remains the Claude Code marketplace entry point.
- The public plugin is skills-only. Agent CLIs and MCP servers require separate
  installation and host configuration.
- `skills/cancer-predisposition-variant-analyst` is an optional git submodule;
  do not count it as part of archive or plugin installs unless it is populated.
