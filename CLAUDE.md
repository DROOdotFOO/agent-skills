# CLAUDE.md

## Project Overview

Agent-skills: 40 Claude Code skills and 7 autonomous agents for polyglot development, web3, ZK, UI/UX, and systems programming. Skills provide context-injection for Claude Code sessions. Agents are standalone tools with CLIs and MCP servers.

## Structure

```
skills/                   # 40 Claude Code skills (context-injection via SKILL.md)
  <name>/SKILL.md         # Entry point per skill, with frontmatter + trigger clauses
agents/                   # 7 autonomous agents (standalone tools)
  digest/                 # Multi-platform activity digest (8 sources)
  recall/                 # Knowledge capture + FTS5 search + MCP server
  autoresearch/           # Domain-agnostic autonomous experiment runner
  watchdog/               # Continuous repo health monitor
  prepper/                # Pre-session context builder
  sentinel/               # On-chain contract monitor
  patchbot/               # Polyglot dependency updater
scripts/                  # Repo tooling (skills-lint.sh)
.claude-plugin/           # Plugin distribution (plugin.json, marketplace.json)
```

## Skills

40 skills across 4 categories. Each lives in `skills/<name>/` with a `SKILL.md` entry point. Sub-files use YAML frontmatter with `impact`, `impactDescription`, and `tags` fields.

**Domain** (9): claude-api, droo-stack, raxol, noir, solidity-audit, ethskills, design-ux, nix, native-code

**Workflow** (11): tdd, code-review, prd-to-plan, prd-to-issues, triage-issue, focused-fix, release, qa, design-an-interface, ubiquitous-language, grill-me

**Infrastructure** (10): mcp-server-builder, ci-cd-pipeline-builder, dependency-auditor, observability-designer, database-designer, performance-profiler, git-guardrails, git-worktree-manager, env-secrets-manager, tech-debt-tracker

**Meta** (10): polymath, architect, agent-designer, adversarial-reviewer, self-improving-agent, codebase-onboarding, rag-architect, llm-cost-optimizer, digest, recall

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

7 agents, each self-contained with Typer CLI, pydantic models, and tests. Install: `cd agents/<name> && pip install -e ".[dev]"`

| Agent        | CLI            | Key commands                                                                              |
| ------------ | -------------- | ----------------------------------------------------------------------------------------- |
| digest       | `digest`       | `generate <topic> [-p hn,github,reddit,youtube,ethresearch,snapshot,polymarket,packages]` |
| recall       | `recall`       | `add`, `search`, `list`, `get`, `delete`, `stale`, `stats`, `extract`, `serve` (MCP)      |
| autoresearch | `autoresearch` | `init <name> --metric <m> --verify <cmd>`, `run`, `loop`, `dashboard`, `status`           |
| watchdog     | `watchdog`     | `scan <repo>`, `report`, `watch --config watchdog.toml`                                   |
| prepper      | `prepper`      | `brief`, `inject` (writes to .claude/prepper-briefing.md)                                 |
| sentinel     | `sentinel`     | `check --address 0x...`, `watch --config sentinel.toml`, `alerts`                         |
| patchbot     | `patchbot`     | `scan`, `update`, `pr`                                                                    |

### Tests

```bash
cd agents/<name> && python -m pytest tests/ -v
```

253 tests total across all agents, 0 mocks.

## Conventions

- Markdown files use YAML frontmatter
- Skills use `SKILL.md` as entry point; agents use `README.md`
- No mocks in tests
- Shell scripts: `set -euo pipefail`, shellcheck compliant
- Python: type hints, pathlib, pydantic, ruff for lint+format
- TypeScript: strict mode, zod for validation
