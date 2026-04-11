"""FastMCP server exposing patchbot tools for Claude Code integration."""

from __future__ import annotations

from fastmcp import FastMCP

from patchbot.detector import detect_ecosystems, get_test_command, get_update_command
from patchbot.models import Ecosystem, UpdatePlan
from patchbot.updater import scan_outdated


def create_server() -> FastMCP:
    """Create a FastMCP server with patchbot tools."""
    mcp = FastMCP(
        "patchbot",
        instructions=(
            "Polyglot dependency updater. Use patchbot_scan to detect ecosystems and list "
            "outdated dependencies. Supports Elixir, Rust, Node, Go, and Python. "
            "Use patchbot_outdated for a specific ecosystem."
        ),
    )

    @mcp.tool()
    def patchbot_scan(repo_path: str = ".") -> str:
        """Detect ecosystems present in a repo and list outdated dependencies for each.

        Args:
            repo_path: Path to the repository (default: current directory)
        """
        ecosystems = detect_ecosystems(repo_path)
        if not ecosystems:
            return "No supported ecosystems detected."

        lines = [f"Detected ecosystems: {', '.join(e.value for e in ecosystems)}\n"]

        for eco in ecosystems:
            deps = scan_outdated(repo_path, eco)
            if not deps:
                lines.append(f"{eco.value}: all up to date (or command unavailable)")
                continue

            lines.append(f"{eco.value}: {len(deps)} outdated")
            for dep in deps:
                latest = dep.latest_version or "?"
                lines.append(f"  {dep.name}: {dep.current_version} -> {latest}")
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    def patchbot_outdated(
        repo_path: str = ".",
        ecosystem: str = "node",
    ) -> str:
        """List outdated dependencies for a specific ecosystem.

        Args:
            repo_path: Path to the repository (default: current directory)
            ecosystem: Ecosystem to check: elixir, rust, node, go, python
        """
        try:
            eco = Ecosystem(ecosystem)
        except ValueError:
            available = ", ".join(e.value for e in Ecosystem)
            return f"Unknown ecosystem: {ecosystem}. Available: {available}"

        detected = detect_ecosystems(repo_path)
        if eco not in detected:
            found = ", ".join(e.value for e in detected)
            return f"Ecosystem {ecosystem} not found in repo. Detected: {found}"

        deps = scan_outdated(repo_path, eco)
        if not deps:
            return f"{ecosystem}: all up to date (or command unavailable)"

        lines = [f"{ecosystem}: {len(deps)} outdated"]
        for dep in deps:
            latest = dep.latest_version or "?"
            lines.append(f"  {dep.name}: {dep.current_version} -> {latest}")

        return "\n".join(lines)

    @mcp.tool()
    def patchbot_update(
        repo_path: str = ".",
        ecosystem: str = "node",
        dry_run: bool = True,
    ) -> str:
        """Run dependency update and tests for an ecosystem.

        Args:
            repo_path: Path to the repository (default: current directory)
            ecosystem: Ecosystem to update: elixir, rust, node, go, python
            dry_run: Preview without executing (default: true for safety)
        """
        from patchbot.updater import run_update

        try:
            eco = Ecosystem(ecosystem)
        except ValueError:
            return f"Unknown ecosystem: {ecosystem}."

        deps = scan_outdated(repo_path, eco)
        plan = UpdatePlan(
            ecosystem=eco,
            dependencies=deps,
            update_command=get_update_command(eco),
            test_command=get_test_command(eco),
        )

        if dry_run:
            return (
                f"Dry run for {ecosystem}:\n"
                f"  Would update {len(deps)} dependencies\n"
                f"  Update command: {plan.update_command}\n"
                f"  Test command: {plan.test_command}"
            )

        result = run_update(repo_path, plan, dry_run=False)

        if result.success and result.test_passed:
            return f"{ecosystem}: updated successfully, tests passed."
        elif result.success:
            return f"{ecosystem}: updated but tests FAILED."
        else:
            return f"{ecosystem}: update failed."

    return mcp
