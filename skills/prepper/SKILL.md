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
  argument-hint: "[--repo owner/repo] [--project name]"
---

# Prepper

Pre-session context builder. Gathers git activity, GitHub state, CI status,
dependency health, and recall knowledge into a priority-sorted briefing.

## What You Get

- Priority-sorted briefing with HIGH/MEDIUM/LOW sections
- Git activity summary (recent commits, branch state)
- GitHub state (open PRs, issues, CI status)
- Dependency health and recall context
- Markdown file or raw terminal output

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

# Cross-agent alert view
prepper alerts --agent sentinel --limit 20
```

## Reference

| File | Topic |
|------|-------|
| [mcp-setup.md](mcp-setup.md) | MCP server, auto-inject hook, install |
