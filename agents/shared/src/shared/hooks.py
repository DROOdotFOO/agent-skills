"""Shared AARTS hook primitives.

Verdict, HookResult, and log_hook_result are used by all agents with
AARTS hooks (recall, autoresearch, patchbot, scribe).

INJECTION_PATTERNS are used by recall (PreMemoryWrite), digest (PostToolUse),
and prepper (PreMemoryRead) for prompt injection scanning.
"""

from __future__ import annotations

import sys
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


def log_hook_result(result: HookResult, *, log_all: bool = False) -> None:
    """Log hook verdicts to stderr.

    By default, logs only ASK verdicts. With log_all=True, logs all
    non-ALLOW verdicts (used by scribe).
    """
    if log_all and result.verdict != Verdict.ALLOW:
        print(
            f"[HOOK] {result.hook}: {result.reason} (verdict={result.verdict.value})",
            file=sys.stderr,
        )
    elif result.verdict == Verdict.ASK:
        print(
            f"[HOOK] {result.hook}: {result.reason} "
            "-- proceeding (ASK verdict, no interactive prompt available)",
            file=sys.stderr,
        )


# Patterns that indicate prompt injection attempts.
# Used by recall (PreMemoryWrite), digest (PostToolUse), prepper (PreMemoryRead).
INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"<\s*system\s*>", "XML system tag"),
    (r"<\s*/\s*system\s*>", "XML system close tag"),
    (r"<\s*instructions?\s*>", "XML instructions tag"),
    (r"<\s*tool_use\s*>", "XML tool_use tag"),
    (r"\[INST\]", "instruction delimiter"),
    (r"<<\s*SYS\s*>>", "Llama system delimiter"),
    (r"(?i)ignore\s+(all\s+)?previous\s+instructions?", "instruction override attempt"),
    (r"(?i)you\s+are\s+now\s+(?:a|an)\b", "role reassignment attempt"),
    (
        r"(?i)forget\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?instructions?",
        "instruction override attempt",
    ),
    (r"(?i)new\s+system\s+prompt", "system prompt injection"),
]
