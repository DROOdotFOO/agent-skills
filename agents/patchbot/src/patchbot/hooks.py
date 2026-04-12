"""AARTS Level 1 hooks for patchbot.

PreToolUse: validates shell commands against known update/test/outdated commands
and safe git/gh operations.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel


class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class HookResult(BaseModel):
    """Result of a hook evaluation."""

    verdict: Verdict
    hook: str
    reason: str


# Known-safe commands that patchbot should be able to run.
# Derived from detector.py UPDATE_COMMANDS, TEST_COMMANDS, OUTDATED_COMMANDS,
# plus git/gh operations from updater.py.
ALLOWLIST: list[str] = [
    # Elixir
    r"^mix\s+hex\.outdated\b",
    r"^mix\s+deps\.update\b",
    r"^mix\s+test\b",
    # Rust
    r"^cargo\s+outdated\b",
    r"^cargo\s+update\b",
    r"^cargo\s+test\b",
    # Node
    r"^npm\s+outdated\b",
    r"^npm\s+update\b",
    r"^npm\s+test\b",
    # Go
    r"^go\s+list\b",
    r"^go\s+get\s+-u\b",
    r"^go\s+test\b",
    # Python
    r"^pip\s+list\s+--outdated\b",
    r"^pip\s+install\s+--upgrade\s+-r\s+requirements\.txt\b",
    r"^pytest\b",
    # Git operations (branch, add, commit, push for PR creation)
    r"^git\s+checkout\s+-b\s+patchbot/",
    r"^git\s+add\s+-A\b",
    r"^git\s+commit\s+-m\b",
    r"^git\s+push\s+-u\s+origin\s+patchbot/",
    # GitHub CLI for PR creation
    r"^gh\s+pr\s+create\b",
]

DENY_LIST: list[str] = [
    r"\bcurl\b",
    r"\bwget\b",
    r"\bssh\b",
    r"\bsudo\b",
    r"\brm\s+-rf\b",
    r"\beval\b",
    r"\bexec\b",
    r"\bgit\s+push\s+--force\b",
    r"\bgit\s+push\s+-f\b",
    r"\bgit\s+reset\s+--hard\b",
]


def pre_tool_use(command: str) -> HookResult:
    """Validate a shell command before execution.

    Patchbot runs outdated checks, dependency updates, test suites,
    and git/gh for PR creation. Only these known commands are allowed.
    """
    cmd = command.strip()

    for pattern in DENY_LIST:
        if re.search(pattern, cmd):
            return HookResult(
                verdict=Verdict.DENY,
                hook="PreToolUse",
                reason=f"command matches deny pattern: {pattern}",
            )

    for pattern in ALLOWLIST:
        if re.search(pattern, cmd):
            return HookResult(
                verdict=Verdict.ALLOW,
                hook="PreToolUse",
                reason=f"command matches allow pattern: {pattern}",
            )

    return HookResult(
        verdict=Verdict.ASK,
        hook="PreToolUse",
        reason=f"command not in allowlist: {cmd[:80]}",
    )
