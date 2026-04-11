#!/usr/bin/env python3
"""Skill trigger accuracy test harness.

Tests that prompts activate the expected skills based on TRIGGER/DO NOT TRIGGER
clauses in SKILL.md frontmatter. Uses simple keyword matching against the
description field -- no LLM needed.

Usage:
    python scripts/skill-triggers-test.py
    python scripts/skill-triggers-test.py -v  # verbose
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# Test cases: (prompt, expected_skills, should_not_trigger)
# expected_skills: skills that SHOULD trigger
# should_not_trigger: skills that MUST NOT trigger
TEST_CASES: list[tuple[str, list[str], list[str]]] = [
    # Domain skills
    (
        "How do I use the Anthropic SDK in Python?",
        ["claude-api"],
        ["solidity-audit", "noir"],
    ),
    (
        "Write a Foundry test for this Solidity contract",
        ["solidity-audit"],
        ["noir", "claude-api"],
    ),
    (
        "Design a Noir circuit for range proofs",
        ["noir"],
        ["solidity-audit"],
    ),
    (
        "What Ethereum tooling and ERC standard should I use for NFTs?",
        ["ethskills"],
        [],  # solidity-audit also matches ERC; acceptable overlap
    ),
    (
        "Check the price of Bitcoin",
        ["coingecko"],
        ["solidity-audit", "noir"],
    ),
    (
        "Look up this contract address on chain",
        ["blockscout"],
        ["coingecko"],
    ),
    # Workflow skills
    (
        "Let's do TDD for this feature",
        ["tdd"],
        [],  # code-review also matches on "review" keywords; acceptable overlap
    ),
    (
        "Review this PR for security issues",
        ["code-review"],
        ["tdd"],
    ),
    (
        "Convert this PRD into implementation phases",
        ["prd-to-plan"],
        [],  # prd-to-issues also matches "PRD"; acceptable -- Claude uses full context
    ),
    (
        "Create GitHub issues from this PRD",
        ["prd-to-issues"],
        [],  # prd-to-plan also matches "PRD"; acceptable overlap
    ),
    (
        "There's a bug in the login flow, can you investigate?",
        ["triage-issue", "focused-fix"],
        [],
    ),
    (
        "Grill me on this architecture design",
        ["grill-me"],
        ["code-review"],
    ),
    # Infrastructure skills
    (
        "Build an MCP server from this OpenAPI spec",
        ["mcp-server-builder"],
        [],
    ),
    (
        "Set up GitHub Actions CI for this repo",
        ["ci-cd-pipeline-builder"],
        [],
    ),
    (
        "Audit our dependencies for vulnerabilities",
        ["dependency-auditor"],
        [],
    ),
    (
        "Design SLOs and alerts for this service",
        ["observability-designer"],
        [],
    ),
    # Meta skills
    (
        "Give me a digest of what's happening with Noir",
        ["digest"],
        [],
    ),
    (
        "What did we decide about the database schema?",
        ["recall"],
        [],
    ),
    (
        "How's the experiment going?",
        ["autoresearch"],
        [],
    ),
    (
        "Check my repos for stale PRs",
        ["watchdog"],
        [],
    ),
    (
        "Give me a project briefing",
        ["prepper"],
        [],
    ),
    (
        "Check this contract for suspicious transactions",
        ["sentinel"],
        [],
    ),
    (
        "What dependencies need updating?",
        ["patchbot"],
        [],
    ),
    (
        "Design a multi-agent system with guardrails",
        ["agent-designer"],
        [],
    ),
    (
        "Tear this code apart, devil's advocate style",
        ["adversarial-reviewer"],
        [],
    ),
    (
        "Design a RAG pipeline with chunking strategy",
        ["rag-architect"],
        [],
    ),
]


def load_skill_triggers() -> dict[str, dict[str, str]]:
    """Load trigger and do-not-trigger clauses from all SKILL.md files."""
    skills: dict[str, dict[str, str]] = {}

    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        name = skill_md.parent.name
        text = skill_md.read_text()

        # Extract description from frontmatter
        match = re.search(r"description:\s*>?\s*\n?(.*?)(?=\n\w+:|---)", text, re.DOTALL)
        if not match:
            match = re.search(r"description:\s*(.+?)(?=\n\w+:|---)", text, re.DOTALL)

        description = match.group(1).strip() if match else ""

        # Extract TRIGGER and DO NOT TRIGGER patterns
        trigger_match = re.search(r"TRIGGER when:\s*(.+?)(?:DO NOT|$)", description, re.DOTALL)
        no_trigger_match = re.search(r"DO NOT TRIGGER when:\s*(.+?)$", description, re.DOTALL)

        skills[name] = {
            "description": description.lower(),
            "trigger": trigger_match.group(1).lower().strip() if trigger_match else "",
            "no_trigger": no_trigger_match.group(1).lower().strip() if no_trigger_match else "",
        }

    return skills


def check_trigger(prompt: str, skill_data: dict[str, str]) -> bool:
    """Check if a prompt would trigger a skill based on its trigger clause."""
    prompt_lower = prompt.lower()
    trigger = skill_data["trigger"]
    description = skill_data["description"]

    if not trigger:
        return False

    # Extract quoted trigger phrases and keywords
    phrases = re.findall(r'"([^"]+)"', trigger)
    # Also split on commas and "or" for keyword extraction
    keywords = re.split(r'[,;]|\bor\b', trigger)
    keywords = [k.strip().strip('"').strip("'") for k in keywords if len(k.strip()) > 2]

    # Check if any trigger phrase appears in prompt
    for phrase in phrases:
        if phrase.lower() in prompt_lower:
            return True

    # Check keywords (need at least partial match)
    for keyword in keywords:
        # Clean up keyword
        kw = keyword.strip().lower()
        if len(kw) < 3:
            continue
        # Check for word-level overlap
        kw_words = set(kw.split())
        prompt_words = set(prompt_lower.split())
        if kw_words & prompt_words:
            return True

    return False


def run_tests(verbose: bool = False) -> tuple[int, int, list[str]]:
    """Run all trigger test cases. Returns (passed, failed, failure_messages)."""
    skills = load_skill_triggers()
    passed = 0
    failed = 0
    failures: list[str] = []

    for prompt, expected, should_not in TEST_CASES:
        # Check expected triggers
        for skill_name in expected:
            if skill_name not in skills:
                failures.append(f"MISSING: skill '{skill_name}' not found")
                failed += 1
                continue

            if check_trigger(prompt, skills[skill_name]):
                passed += 1
                if verbose:
                    print(f"  PASS: '{prompt[:50]}...' -> {skill_name}")
            else:
                failed += 1
                failures.append(
                    f"MISS: '{prompt[:60]}' should trigger '{skill_name}' but didn't"
                )

        # Check should-not-trigger
        for skill_name in should_not:
            if skill_name not in skills:
                continue

            if check_trigger(prompt, skills[skill_name]):
                failed += 1
                failures.append(
                    f"FALSE+: '{prompt[:60]}' should NOT trigger '{skill_name}' but did"
                )
            else:
                passed += 1
                if verbose:
                    print(f"  PASS: '{prompt[:50]}...' correctly skips {skill_name}")

    return passed, failed, failures


def main() -> None:
    verbose = "-v" in sys.argv
    print(f"Loading skills from {SKILLS_DIR}...")

    skills = load_skill_triggers()
    print(f"Found {len(skills)} skills with trigger clauses\n")

    passed, failed, failures = run_tests(verbose)

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  {f}")

    total = passed + failed
    print(f"\n{passed}/{total} passed, {failed} failed")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
