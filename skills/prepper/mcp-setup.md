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

Add to `~/.mcp.json`:

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
| `prepper_inject` | Generate and write briefing to .claude/prepper-briefing.md  |
| `prepper_alerts` | Unified cross-agent alert view with agent filter            |

## Auto-inject on SessionStart

Add to your project's `.claude/settings.json`:

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

This generates a briefing at session start and injects it as context.
For more control (repo/project detection), use the hook script:

```json
"command": "~/.agents/skills-repo/scripts/hooks/prepper-session-start.sh"
```

## Install

```bash
cd agents/prepper
pip install -e .
```

Optional: `gh` CLI for GitHub state, `recall` CLI for knowledge base integration.
