---
name: prepper
description: >
  Generate pre-session project briefings with git activity, GitHub state, CI status,
  dependency health, and recall context.
  TRIGGER when: user asks for a "briefing", "what's the state of this project",
  "catch me up", "prep me", or invokes "/prepper".
  DO NOT TRIGGER when: user is working on prepper agent code itself.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: prepper, briefing, context, session
---

# Prepper

Pre-session context builder. Gathers git activity, GitHub state, CI status,
dependency health, and recall knowledge into a priority-sorted briefing.

## CLI Usage

```bash
# Generate briefing for current repo
prepper brief

# With GitHub integration and recall context
prepper brief --repo owner/repo --project myproject

# Write to file
prepper brief --output briefing.md

# Inject into .claude/prepper-briefing.md for auto-loading
prepper inject --repo owner/repo --project myproject
```

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

| Tool | Description |
|------|-------------|
| `prepper_brief` | Generate a project briefing (git, GitHub, CI, deps, recall) |
| `prepper_inject` | Generate and write briefing to .claude/prepper-briefing.md |

## Auto-inject on SessionStart

Add to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{
        "type": "command",
        "command": "prepper brief --raw",
        "timeout": 30
      }]
    }]
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
