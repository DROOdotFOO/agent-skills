# agent-skills

47 Claude Code skills and 7 autonomous agents for polyglot development, web3, ZK, UI/UX, and systems programming.

## Skills

Context-injection skills for Claude Code sessions. Each skill lives in `skills/<name>/` with a `SKILL.md` entry point.

### Domain skills

| Skill            | Description                                                                         |
| ---------------- | ----------------------------------------------------------------------------------- |
| `claude-api`     | Anthropic SDK reference (Python, TS, Go, Elixir, Rust, Lua, cURL)                   |
| `droo-stack`     | Polyglot patterns (Elixir, TS, Go, Rust, C, Zig, Python, Lua, Shell, Noir, Chezmoi) |
| `raxol`          | Elixir TUI/agent framework (TEA agents, MCP, headless sessions)                     |
| `noir`           | ZK circuit design, Aztec contracts, constraint optimization                         |
| `solidity-audit` | Solidity dev standards, vulnerability taxonomy, Foundry-first audit                 |
| `ethskills`      | Ethereum tooling, framework selection, EIP/ERC standards                            |
| `design-ux`      | UI/UX design patterns, design tokens, accessibility, TUI aesthetics                 |
| `nix`            | Nix language, flakes, NixOS, Home Manager, packaging                                |
| `native-code`    | NIF development (C/Rust/Rustler), SIMD (Zig), BEAM native boundary                  |
| `coingecko`      | CoinGecko/GeckoTerminal API: prices, markets, DEX pools, trending tokens             |
| `blockscout`     | Blockscout MCP tool reference: 16 tools for on-chain data across 8+ chains           |

### Workflow skills

| Skill                 | Description                                                             |
| --------------------- | ----------------------------------------------------------------------- |
| `tdd`                 | Test-driven development: vertical slices, mutation testing, polyglot    |
| `code-review`         | PR review: blast radius, security scan, SOLID checks, 40-item checklist |
| `prd-to-plan`         | PRD -> phased tracer-bullet vertical slices                             |
| `prd-to-issues`       | PRD -> GitHub issues with HITL/AFK classification                       |
| `triage-issue`        | Bug investigation -> GitHub issue with TDD fix plan                     |
| `focused-fix`         | 5-phase bug fix: SCOPE -> TRACE -> DIAGNOSE -> FIX -> VERIFY            |
| `release`             | Conventional commits, semver bumping, changelog, readiness checks       |
| `qa`                  | Interactive QA with background explorer, issue filing                   |
| `design-an-interface` | "Design It Twice" -- parallel sub-agents with divergent constraints     |
| `ubiquitous-language` | DDD glossary extraction, canonical terms                                |
| `grill-me`            | Stress-test designs via structured interrogation                        |

### Infrastructure skills

| Skill                    | Description                                                     |
| ------------------------ | --------------------------------------------------------------- |
| `mcp-server-builder`     | OpenAPI -> MCP server scaffolding (Python FastMCP + TypeScript) |
| `ci-cd-pipeline-builder` | Stack detection -> GitHub Actions/GitLab CI generation          |
| `dependency-auditor`     | Multi-language vuln scanning + license compliance               |
| `observability-designer` | SLO/SLI design, burn rate alerting, dashboard generation        |
| `database-designer`      | Schema analysis, ERD generation, index optimization             |
| `performance-profiler`   | Polyglot profiling (Node/Python/Go/Elixir/Rust)                 |
| `git-guardrails`         | PreToolUse hooks to block dangerous git operations              |
| `git-worktree-manager`   | Parallel dev with deterministic port allocation                 |
| `env-secrets-manager`    | Leak detection, rotation, pre-commit setup                      |
| `tech-debt-tracker`      | Debt scanning, cost-of-delay prioritization                     |

### Meta skills

| Skill                  | Description                                                           |
| ---------------------- | --------------------------------------------------------------------- |
| `polymath`             | Split-brain research: three-tier roster, polymath persona composition |
| `architect`            | ADR workflows, dependency classification, pattern detection           |
| `agent-designer`       | Multi-agent architecture patterns, tool schemas, guardrails           |
| `adversarial-reviewer` | Three-persona devil's advocate review                                 |
| `self-improving-agent` | Auto-memory curation, pattern promotion lifecycle                     |
| `codebase-onboarding`  | Auto-generate onboarding docs, audience-aware                         |
| `rag-architect`        | RAG pipeline design: chunking, embedding, retrieval, evaluation       |
| `llm-cost-optimizer`   | 6 optimization techniques in priority order                           |
| `digest`               | Multi-platform activity digest (9 sources + differential mode)        |
| `recall`               | Knowledge base: query past decisions, patterns, gotchas               |
| `autoresearch`         | Check experiment status, run iterations, view dashboards              |
| `watchdog`             | Scan repos for stale PRs, failing CI, security advisories             |
| `prepper`              | Generate pre-session project briefings                                |
| `sentinel`             | Monitor on-chain contracts for anomalous transactions                 |
| `patchbot`             | Scan and update outdated dependencies across ecosystems               |

## Agents

Autonomous tools that run independently. Each agent lives in `agents/<name>/`. All agents expose MCP servers via `<agent> serve` (stdio transport) for direct Claude Code integration.

| Agent          | Description                                                         | MCP tools | Status   |
| -------------- | ------------------------------------------------------------------- | --------- | -------- |
| `digest`       | Multi-platform activity digest (9 sources, differential, structured views) | 6   | MVP done |
| `recall`       | Knowledge capture and retrieval (SQLite + FTS5 + MCP server)        | 8         | MVP done |
| `autoresearch` | Domain-agnostic autonomous experiment runner (ML, Noir, Solidity)   | 3         | MVP done |
| `watchdog`     | Continuous repo health monitor (PRs, CI, deps, advisories)          | 2         | MVP done |
| `prepper`      | Pre-session context builder (git, GitHub, deps, recall, sentinel, digest) | 2   | MVP done |
| `sentinel`     | On-chain contract monitor via Blockscout API (11 chains)            | 2         | MVP done |
| `patchbot`     | Polyglot dependency updater (Elixir, Rust, Node, Go, Python)        | 3         | MVP done |

### MCP integration

Each agent can run as an MCP server for Claude Code. Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "digest":       { "command": "digest",       "args": ["serve"] },
    "recall":       { "command": "recall",       "args": ["serve"] },
    "autoresearch": { "command": "autoresearch", "args": ["serve"] },
    "watchdog":     { "command": "watchdog",     "args": ["serve"] },
    "prepper":      { "command": "prepper",      "args": ["serve"] },
    "sentinel":     { "command": "sentinel",     "args": ["serve"] },
    "patchbot":     { "command": "patchbot",     "args": ["serve"] },
    "coingecko":    { "url": "https://mcp.api.coingecko.com/mcp" }
  }
}
```

See [TODO.md](TODO.md) for the full roadmap.

## Installation

### Claude Code plugin (recommended)

```bash
/plugin install agent-skills@DROOdotFOO/agent-skills
```

Or add to your Claude Code marketplace:

```bash
/plugin marketplace add DROOdotFOO/agent-skills
```

### npx skills CLI

Install individual skills:

```bash
npx skills@latest add DROOdotFOO/agent-skills/tdd
npx skills@latest add DROOdotFOO/agent-skills/code-review
npx skills@latest add DROOdotFOO/agent-skills/polymath
```

Or install all:

```bash
npx skills@latest add DROOdotFOO/agent-skills
```

### With chezmoi

Add to your `.chezmoiexternal.toml`:

```toml
[".agents/skills"]
    type = "archive"
    url = "https://github.com/DROOdotFOO/agent-skills/archive/main.tar.gz"
    stripComponents = 2
    include = ["*/skills/**"]
    refreshPeriod = "168h"
```

Then symlink to Claude Code's skills directory:

```bash
mkdir -p ~/.claude/skills
for d in ~/.agents/skills/*/; do
    ln -sf "../../.agents/skills/$(basename "$d")" ~/.claude/skills/
done
```

### Manual

```bash
git clone https://github.com/DROOdotFOO/agent-skills.git ~/.agents/skills-repo
ln -s ~/.agents/skills-repo/skills ~/.agents/skills
```

### Agents

Install each agent independently:

```bash
cd agents/<name> && pip install -e .
```

## Linting

```bash
./scripts/skills-lint.sh
```

Validates frontmatter, trigger clauses, file references, and cross-skill links.

## License

MIT
