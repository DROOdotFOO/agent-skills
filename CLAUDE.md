# CLAUDE.md

## Project Overview

Agent-skills: Claude Code skills and autonomous agents. Skills provide context-injection for Claude Code sessions. Agents are autonomous tools that run independently.

## Structure

```
skills/           # Claude Code skills (context-injection via SKILL.md)
  <name>/SKILL.md # Entry point per skill, with frontmatter + trigger clauses
agents/           # Autonomous agents (standalone tools)
  <name>/         # Each agent is self-contained
scripts/          # Repo tooling (linting, etc.)
```

## Skills

Each skill lives in `skills/<name>/` with a `SKILL.md` entry point. Sub-files use YAML frontmatter with `impact`, `impactDescription`, and `tags` fields.

### Lint

```bash
./scripts/skills-lint.sh
```

Validates: frontmatter fields, trigger clauses, file references, cross-skill links.

### Adding a skill

1. Create `skills/<name>/SKILL.md` with frontmatter: `name`, `description` (include `TRIGGER when:` / `DO NOT TRIGGER`), `metadata`
2. Add sub-files with YAML frontmatter (`impact`, `impactDescription`, `tags` as comma-separated string)
3. Run `./scripts/skills-lint.sh`

## Agents

Each agent lives in `agents/<name>/` and is self-contained. See `TODO.md` for the roadmap.

### Planned agents

- **digest** -- Multi-platform activity digest (inspired by last30days-skill)
- **recall** -- Knowledge capture and retrieval (inspired by paperclip)
- **autoresearch** -- Autonomous ML experiment runner (inspired by karpathy/autoresearch)

## Conventions

- Markdown files use YAML frontmatter
- Skills use `SKILL.md` as entry point; agents use `README.md`
- No mocks in tests
- Shell scripts: `set -euo pipefail`, shellcheck compliant
- Python: type hints, pathlib, pydantic
- TypeScript: strict mode, zod for validation
