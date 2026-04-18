"""AARTS Level 1 hooks for recall.

PreMemoryWrite: scans content for injection patterns and credential strings
before allowing persistence to the FTS5 store.
"""

from __future__ import annotations

import re

from shared.hooks import (
    INJECTION_PATTERNS,
    HookResult,
    Verdict,
    log_hook_result,
)

# Patterns that look like credentials or secrets
CREDENTIAL_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)(?:api[_-]?key|apikey)\s*[:=]\s*\S{16,}", "API key"),
    (r"(?i)(?:secret|password|passwd|token)\s*[:=]\s*\S{8,}", "secret/password/token"),
    (r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}", "GitHub token"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI/Anthropic API key"),
    (r"(?:AKIA|ASIA)[A-Z0-9]{16}", "AWS access key"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "private key"),
    (r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}", "bearer token"),
]


def pre_memory_write(content: str) -> HookResult:
    """Scan content before writing to the recall store.

    Checks for prompt injection patterns and credential strings.
    Injection attempts are denied. Credential-like content triggers ASK
    so the user can confirm it's intentional.
    """
    # Check injection patterns -- hard deny
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, content):
            return HookResult(
                verdict=Verdict.DENY,
                hook="PreMemoryWrite",
                reason=f"content contains {description}",
            )

    # Check credential patterns -- ask user
    for pattern, description in CREDENTIAL_PATTERNS:
        if re.search(pattern, content):
            return HookResult(
                verdict=Verdict.ASK,
                hook="PreMemoryWrite",
                reason=f"content may contain {description}",
            )

    return HookResult(
        verdict=Verdict.ALLOW,
        hook="PreMemoryWrite",
        reason="content passed safety checks",
    )


__all__ = ["Verdict", "HookResult", "log_hook_result", "pre_memory_write"]
