---
name: git-guardrails
description: >
  Set up Codex or Claude Code hooks to block dangerous git commands before they execute.
  TRIGGER when: user wants to prevent destructive git operations, add git safety hooks,
  or block git push/reset in an agent coding host.
  DO NOT TRIGGER when: user is asking about git workflow or branching strategy.
metadata:
  author: mattpocock
  version: "1.0.0"
  tags: git, safety, hooks, PreToolUse, destructive-operations
  license: MIT
---

# Git Guardrails

Sets up a PreToolUse hook that intercepts and blocks dangerous git commands before the coding agent executes them.

## What You Get

- PreToolUse hook blocking destructive git operations
- Project-scoped or global installation
- Customizable blocked command patterns
- Verification test command

## What Gets Blocked

- `git push` (all variants including `--force`)
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .`

When blocked, the host receives a message explaining why the command is denied.

## WRONG: no guardrails, Claude runs destructive commands silently

```bash
# The coding agent decides to "clean up" and runs:
git reset --hard HEAD~3   # 3 commits of work gone
git clean -fd             # untracked files deleted
git push --force          # rewrites shared history
```

## CORRECT: hook blocks before execution

```
$ echo '{"tool_input":{"command":"git push --force"}}' | block-dangerous-git.sh
BLOCKED: git push is not allowed. Ask the user to run it manually.
```

## Setup Steps

1. **Identify host and scope** -- Codex or Claude Code; project or global.
2. **Copy hook script** -- bundled at [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh). Put it in the host's project or global hooks directory and make it executable.
3. **Add to settings** -- see [settings-config.md](settings-config.md) for Codex and Claude Code examples.
4. **Customize** -- ask if user wants to add/remove patterns from the blocked list
5. **Verify** -- `echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>` should exit code 2 with BLOCKED message

## Reference

| File | Topic |
|------|-------|
| [settings-config.md](settings-config.md) | Codex and Claude Code hook configuration |
| [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh) | The hook script |
