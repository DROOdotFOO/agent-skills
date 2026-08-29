#!/usr/bin/env bash
# Codex/Claude Code SessionStart hook: generate a prepper briefing for context.
#
# Install through .codex/hooks.json or .claude/settings.json:
#
#   {
#     "hooks": {
#       "SessionStart": [{
#         "matcher": "startup",
#         "hooks": [{
#           "type": "command",
#           "command": "prepper brief --raw",
#           "timeout": 30
#         }]
#       }]
#     }
#   }
#
# Or use this script for more control:
#
#   "command": "/path/to/prepper-session-start.sh"
#
# The script checks if prepper is installed, generates a briefing,
# and outputs it to stdout for the host to inject as context.

set -euo pipefail

# Check if prepper is available
if ! command -v prepper &>/dev/null; then
    echo "prepper not installed -- skipping session briefing"
    exit 0
fi

# Detect repo and project name from git
REPO=""
PROJECT=""

if command -v gh &>/dev/null && git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
    PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || true)
fi

# Build the command without eval so repository names cannot become shell syntax.
cmd=(prepper brief --raw)
if [[ -n "$REPO" ]]; then
    cmd+=(--repo "$REPO")
fi
if [[ -n "$PROJECT" ]]; then
    cmd+=(--project "$PROJECT")
fi

# Generate and output briefing (stdout is injected as context)
"${cmd[@]}" 2>/dev/null || echo "prepper briefing failed -- continuing without context"
