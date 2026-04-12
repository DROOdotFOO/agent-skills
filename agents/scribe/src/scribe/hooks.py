"""AARTS hooks for scribe.

Scribe-specific pre-write checks. Recall's Store.add() already calls
pre_memory_write() for injection and credential scanning. This module
adds scribe-specific noise filtering.
"""

from __future__ import annotations

import sys
from enum import Enum

from pydantic import BaseModel

MIN_INSIGHT_LENGTH = 20

# Content that is just tool output or boilerplate
_NOISE_PREFIXES: list[str] = [
    "File created successfully",
    "Successfully installed",
    "Requirement already satisfied",
    "Running",
    "Collecting",
    "Downloading",
]


class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class HookResult(BaseModel):
    verdict: Verdict
    hook: str
    reason: str


def pre_scribe_write(content: str) -> HookResult:
    """Scribe-specific checks before writing to recall.

    - Reject content shorter than MIN_INSIGHT_LENGTH
    - Reject content that is pure tool output
    """
    if len(content.strip()) < MIN_INSIGHT_LENGTH:
        return HookResult(
            verdict=Verdict.DENY,
            hook="PreScribeWrite",
            reason=f"content too short ({len(content.strip())} < {MIN_INSIGHT_LENGTH})",
        )

    for prefix in _NOISE_PREFIXES:
        if content.strip().startswith(prefix):
            return HookResult(
                verdict=Verdict.DENY,
                hook="PreScribeWrite",
                reason=f"content is tool output noise (starts with '{prefix}')",
            )

    return HookResult(
        verdict=Verdict.ALLOW,
        hook="PreScribeWrite",
        reason="content passed scribe checks",
    )


def log_hook_result(result: HookResult) -> None:
    """Log non-ALLOW verdicts to stderr."""
    if result.verdict != Verdict.ALLOW:
        print(
            f"[HOOK] {result.hook}: {result.reason} (verdict={result.verdict.value})",
            file=sys.stderr,
        )
