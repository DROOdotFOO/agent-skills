---
impact: MEDIUM
impactDescription: "MCP server configuration, auto-inject hook setup, and install instructions"
tags: "prepper,mcp,setup,hooks"
---

## MCP Server

```bash
prepper serve
```

### Configure MCP

For Codex, add to `~/.codex/config.toml`:

```toml
[mcp_servers.prepper]
command = "prepper"
args = ["serve"]
```

For Claude Code, add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "prepper": {
      "command": "prepper",
      "args": ["serve"]
    }
  }
}
```

### MCP Tools

| Tool             | Description                                                 |
| ---------------- | ----------------------------------------------------------- |
| `prepper_brief`  | Generate a project briefing (git, GitHub, CI, deps, recall) |
| `prepper_inject` | Generate and write Claude Code's .claude/prepper-briefing.md |
| `prepper_alerts` | Unified cross-agent alert view with agent filter            |

## Auto-inject on SessionStart

For Codex, add to `.codex/hooks.json` or `~/.codex/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "prepper brief --raw",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Review and trust the Codex hook through `/hooks`. For Claude Code, add to the
project's `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "prepper brief --raw",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

This generates a briefing at session start and injects it as context. For more
control (repo/project detection) in either host, use the hook script:

```json
"command": "~/.agents/skills-repo/scripts/hooks/prepper-session-start.sh"
```

## Install

```bash
cd agents/prepper
pip install -e .
```

Optional: `gh` CLI for GitHub state, `recall` CLI for knowledge base integration.
