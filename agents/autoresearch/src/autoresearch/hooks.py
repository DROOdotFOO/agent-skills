"""AARTS Level 1 hooks for autoresearch.

PreToolUse: validates shell commands (verify, guard) against allowlists.
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


# Commands that are always safe for verify/guard.
# Each entry is a regex anchored to the start of the command.
VERIFY_ALLOWLIST: list[str] = [
    r"^cargo\s+test\b",
    r"^cargo\s+bench\b",
    r"^cargo\s+check\b",
    r"^cargo\s+clippy\b",
    r"^cargo\s+build\b",
    r"^python\s+-m\s+pytest\b",
    r"^python\s+-m\s+unittest\b",
    r"^pytest\b",
    r"^nargo\s+test\b",
    r"^nargo\s+check\b",
    r"^nargo\s+compile\b",
    r"^mix\s+test\b",
    r"^mix\s+compile\b",
    r"^go\s+test\b",
    r"^go\s+build\b",
    r"^npm\s+test\b",
    r"^npm\s+run\s+test\b",
    r"^make\b",
    r"^just\b",
]

# Commands explicitly denied (dangerous in experiment context).
DENY_LIST: list[str] = [
    r"\bcurl\b",
    r"\bwget\b",
    r"\bssh\b",
    r"\bscp\b",
    r"\bnc\b",
    r"\bnetcat\b",
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bchmod\b",
    r"\bchown\b",
    r"\bdd\b",
    r"\bmkfs\b",
    r"\beval\b",
    r"\bexec\b",
    r"\bpip\s+install\b",
    r"\bnpm\s+install\b",
    r"\bcargo\s+install\b",
]


def pre_tool_use(command: str) -> HookResult:
    """Validate a shell command before execution.

    Checks verify and guard commands against the allowlist and denylist.
    Returns ALLOW for known-safe commands, DENY for dangerous ones,
    and ASK for anything else (unknown commands that need human review).
    """
    cmd = command.strip()

    # Check denylist first
    for pattern in DENY_LIST:
        if re.search(pattern, cmd):
            return HookResult(
                verdict=Verdict.DENY,
                hook="PreToolUse",
                reason=f"command matches deny pattern: {pattern}",
            )

    # Check allowlist
    for pattern in VERIFY_ALLOWLIST:
        if re.search(pattern, cmd):
            return HookResult(
                verdict=Verdict.ALLOW,
                hook="PreToolUse",
                reason=f"command matches allow pattern: {pattern}",
            )

    # Unknown command -- ask the user
    return HookResult(
        verdict=Verdict.ASK,
        hook="PreToolUse",
        reason=f"command not in allowlist: {cmd[:80]}",
    )
