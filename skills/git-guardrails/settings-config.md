---
impact: HIGH
impactDescription: "JSON settings for project-scoped and global hook configuration"
tags: "git-guardrails,settings,hooks,config"
---

## Settings configuration

The bundled script accepts the shared `tool_input.command` hook field and
blocks by writing the reason to stderr and exiting with status 2.

### Codex project scope (`.codex/hooks.json`)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^Bash$",
        "hooks": [
          {
            "type": "command",
            "command": "$(git rev-parse --show-toplevel)/.codex/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

For global Codex scope, put the configuration in `~/.codex/hooks.json` and
use an absolute command path. Review and trust the hook through `/hooks` after
installing or changing it.

### Claude Code project scope (`.claude/settings.json`)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

### Claude Code global scope (`~/.claude/settings.json`)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

If settings already exist, merge the hook into the existing `hooks.PreToolUse` array.
