#!/usr/bin/env python3
"""Skill benchmark harness.

Measures whether injecting a Claude Code skill as context improves
Claude's code output quality, using AST-based pattern detection.

Usage:
    python benchmarks/skill-bench.py compare --skill skills/droo-stack --suite python-patterns
    python benchmarks/skill-bench.py compare --skill skills/droo-stack --suite python-patterns --runs 3
    python benchmarks/skill-bench.py evaluate --suite python-patterns --code-dir /tmp/bench-outputs
"""

from __future__ import annotations

import importlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Annotated

import anthropic
import typer

app = typer.Typer(help="Skill benchmark harness")

BENCHMARKS_DIR = Path(__file__).parent
SUITES_DIR = BENCHMARKS_DIR / "suites"
ALTERNATIVES_DIR = BENCHMARKS_DIR / "alternatives"
SKILLS_DIR = BENCHMARKS_DIR.parent / "skills"

DEFAULT_MODEL = "claude-sonnet-4-6-20250514"


def load_skill_context(skill_path: Path) -> str:
    """Load skill content from SKILL.md and all sub-files."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        # Treat as a raw file (e.g., alternatives/no-context.md)
        if skill_path.is_file():
            return skill_path.read_text().strip()
        return ""

    parts = [skill_md.read_text()]

    # Load sub-files referenced in the skill
    for md_file in sorted(skill_path.rglob("*.md")):
        if md_file.name == "SKILL.md":
            continue
        parts.append(f"\n\n---\n# {md_file.stem}\n\n{md_file.read_text()}")

    return "\n".join(parts)


def load_suite(suite_name: str) -> list[dict]:
    """Load task definitions from a suite's tasks.json."""
    tasks_file = SUITES_DIR / suite_name / "tasks.json"
    if not tasks_file.exists():
        typer.echo(f"Suite not found: {tasks_file}", err=True)
        raise typer.Exit(1)
    return json.loads(tasks_file.read_text())


def extract_python_code(response_text: str) -> str:
    """Extract Python code blocks from Claude's response."""
    # Match ```python ... ``` blocks
    blocks = re.findall(r"```python\s*\n(.*?)```", response_text, re.DOTALL)
    if blocks:
        return "\n\n".join(blocks)

    # Fall back to any ``` blocks
    blocks = re.findall(r"```\s*\n(.*?)```", response_text, re.DOTALL)
    if blocks:
        return "\n\n".join(blocks)

    # Last resort: return the whole response
    return response_text


def call_claude(
    client: anthropic.Anthropic,
    skill_context: str,
    task_prompt: str,
    model: str,
) -> str:
    """Call Claude API with skill context and task prompt."""
    system_parts = []
    if skill_context:
        system_parts.append(
            "You are a Python expert. Follow these coding guidelines:\n\n" + skill_context
        )
    else:
        system_parts.append("You are a Python expert.")

    system_parts.append(
        "\nRespond with ONLY the Python code in a ```python``` code block. "
        "No explanations, no prose."
    )

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        temperature=0,
        system="\n".join(system_parts),
        messages=[{"role": "user", "content": task_prompt}],
    )
    return response.content[0].text


def run_checks(suite_name: str, test_module_name: str, code: str) -> dict[str, bool]:
    """Run pattern checks against generated code."""
    # Import the test module dynamically
    tests_dir = SUITES_DIR / suite_name / "tests"
    if str(tests_dir.parent) not in sys.path:
        sys.path.insert(0, str(tests_dir.parent))

    module = importlib.import_module(f"tests.{test_module_name}")
    return module.evaluate(code)


def count_tokens(text: str) -> int:
    """Rough token count (words * 1.3)."""
    return int(len(text.split()) * 1.3)


@app.command()
def compare(
    skill: Annotated[str, typer.Option(help="Skill directory path (relative to repo root)")] = "",
    suite: Annotated[str, typer.Option(help="Test suite name")] = "python-patterns",
    runs: Annotated[int, typer.Option(help="Number of runs for stability")] = 1,
    model: Annotated[str, typer.Option(help="Claude model to use")] = DEFAULT_MODEL,
    output: Annotated[Path | None, typer.Option(help="Output results to JSON file")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Run benchmark comparing skill vs no-context baseline."""
    client = anthropic.Anthropic()
    tasks = load_suite(suite)

    # Resolve skill path
    if skill:
        skill_path = Path(skill)
        if not skill_path.is_absolute():
            skill_path = BENCHMARKS_DIR.parent / skill_path
    else:
        skill_path = ALTERNATIVES_DIR / "no-context.md"

    # Load contexts
    skill_context = load_skill_context(skill_path)
    baseline_context = ""

    skill_name = skill_path.name if skill else "no-context"
    tokens_injected = count_tokens(skill_context) if skill_context else 0

    typer.echo(f"Suite: {suite}")
    typer.echo(f"Skill: {skill_name} ({tokens_injected} tokens)")
    typer.echo(f"Tasks: {len(tasks)}")
    typer.echo(f"Runs: {runs}")
    typer.echo(f"Model: {model}")
    typer.echo("---")

    # Run benchmark for each context
    contexts = {"no-context": baseline_context}
    if skill:
        contexts[skill_name] = skill_context

    all_results: dict[str, dict] = {}

    for ctx_name, ctx_content in contexts.items():
        typer.echo(f"\n[{ctx_name}]")
        task_results: list[dict] = []

        for task in tasks:
            check_scores: list[dict[str, bool]] = []

            for run_idx in range(runs):
                typer.echo(f"  {task['id']} run {run_idx + 1}/{runs}...", nl=False)
                start = time.monotonic()

                code = call_claude(client, ctx_content, task["prompt"], model)
                elapsed = time.monotonic() - start

                checks = run_checks(suite, task["test_module"], code)
                check_scores.append(checks)

                passed = sum(checks.values())
                total = len(checks)
                typer.echo(f" {passed}/{total} ({elapsed:.1f}s)")

                if verbose:
                    for check_name, check_passed in checks.items():
                        mark = "+" if check_passed else "-"
                        typer.echo(f"    [{mark}] {check_name}")

            # Aggregate across runs: a check passes if it passed in majority of runs
            aggregated: dict[str, bool] = {}
            for check_name in check_scores[0]:
                pass_count = sum(r[check_name] for r in check_scores)
                aggregated[check_name] = pass_count > runs / 2

            task_results.append(
                {
                    "task_id": task["id"],
                    "checks": aggregated,
                    "passed": sum(aggregated.values()),
                    "total": len(aggregated),
                    "raw_runs": check_scores,
                }
            )

        # Compute aggregate metrics
        total_checks = sum(r["total"] for r in task_results)
        passed_checks = sum(r["passed"] for r in task_results)
        correctness = passed_checks / total_checks if total_checks > 0 else 0.0

        all_results[ctx_name] = {
            "correctness": correctness,
            "passed": passed_checks,
            "total": total_checks,
            "tokens_injected": count_tokens(ctx_content) if ctx_content else 0,
            "tasks": task_results,
        }

    # Output results
    typer.echo("\n===\n")

    # Autoresearch-compatible metric output
    if skill and skill_name in all_results:
        r = all_results[skill_name]
        typer.echo(f"METRIC correctness={r['correctness']:.3f}")
        typer.echo(f"METRIC tokens_injected={r['tokens_injected']}")
        if "no-context" in all_results:
            baseline = all_results["no-context"]["correctness"]
            delta = r["correctness"] - baseline
            typer.echo(f"METRIC delta={delta:.3f}")

    # Comparison table
    typer.echo("")
    typer.echo("| Context | Correctness | Checks | Tokens |")
    typer.echo("|---------|-------------|--------|--------|")
    for ctx_name, r in all_results.items():
        typer.echo(
            f"| {ctx_name:<20s} | {r['correctness']:.2f} | "
            f"{r['passed']}/{r['total']} | {r['tokens_injected']} |"
        )

    # Per-task breakdown
    typer.echo("\nPer-task breakdown:")
    for ctx_name, r in all_results.items():
        typer.echo(f"\n  [{ctx_name}]")
        for task_r in r["tasks"]:
            status = "PASS" if task_r["passed"] == task_r["total"] else "PARTIAL"
            typer.echo(f"    {task_r['task_id']}: {task_r['passed']}/{task_r['total']} {status}")
            for check_name, check_passed in task_r["checks"].items():
                mark = "+" if check_passed else "-"
                typer.echo(f"      [{mark}] {check_name}")

    if output:
        output.write_text(json.dumps(all_results, indent=2))
        typer.echo(f"\nResults written to {output}")


@app.command()
def evaluate(
    suite: Annotated[str, typer.Option(help="Test suite name")] = "python-patterns",
    code_file: Annotated[Path | None, typer.Option(help="File containing code to evaluate")] = None,
    code: Annotated[str | None, typer.Option(help="Inline code to evaluate")] = None,
    task_id: Annotated[str | None, typer.Option(help="Task ID to evaluate against")] = None,
) -> None:
    """Evaluate code against a specific task's checks (no API call needed)."""
    tasks = load_suite(suite)

    if code_file:
        code_str = code_file.read_text()
    elif code:
        code_str = code
    else:
        typer.echo("Provide --code-file or --code", err=True)
        raise typer.Exit(1)

    target_tasks = [t for t in tasks if t["id"] == task_id] if task_id else tasks

    for task in target_tasks:
        checks = run_checks(suite, task["test_module"], code_str)
        passed = sum(checks.values())
        total = len(checks)
        typer.echo(f"{task['id']}: {passed}/{total}")
        for check_name, check_passed in checks.items():
            mark = "+" if check_passed else "-"
            typer.echo(f"  [{mark}] {check_name}")


if __name__ == "__main__":
    app()
