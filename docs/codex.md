# Codex target

Codex can consume this repository in two mutually exclusive ways:

1. Install skills under `~/.agents/skills` for a personal, filesystem-managed setup.
2. Install the `agent-skills` plugin for marketplace distribution.

Do not enable both in the same Codex profile because duplicate skill names are
not merged.

## Plugin development

The plugin entry point is `.codex-plugin/plugin.json`. Validate it from the
repository root:

```bash
python /path/to/plugin-creator/scripts/validate_plugin.py .
python3 scripts/codex-compat-test.py
```

Test installation with an isolated `CODEX_HOME` so the repository's skills do
not collide with personal copies. Start a new session after installing or
updating the plugin.

## MCP agents

The plugin is skills-only. Install an agent CLI separately, then register its
stdio server in `~/.codex/config.toml`:

```toml
[mcp_servers.prepper]
command = "prepper"
args = ["serve"]

[mcp_servers.recall]
command = "recall"
args = ["serve"]
```

The same shape applies to `digest`, `scribe`, `autoresearch`, `watchdog`,
`sentinel`, `patchbot`, and `regen`.

For HTTP MCP servers:

```toml
[mcp_servers.blockscout]
url = "https://mcp.blockscout.com/mcp"

[mcp_servers.coingecko]
url = "https://mcp.api.coingecko.com/mcp"
```

Verify the active inventory with `codex mcp list`.

## Host-specific workflow surfaces

| Concern | Codex | Claude Code |
| --- | --- | --- |
| Repository guidance | `AGENTS.md` | `CLAUDE.md` |
| Personal skills | `~/.agents/skills` | `~/.claude/skills` |
| Hooks | `.codex/hooks.json` or `~/.codex/hooks.json` | `.claude/settings.json` |
| MCP | `~/.codex/config.toml` | `~/.mcp.json` |
| Explicit skill invocation | `$skill-name` | host skill invocation |

Codex requires users to review and trust new or changed non-managed hooks
through `/hooks` before they run.
