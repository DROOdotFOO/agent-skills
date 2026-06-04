"""Detect ecosystems present in a repository."""

from pathlib import Path

from patchbot.models import Dependency, Ecosystem

# Mapping of filename -> ecosystem. Order within each ecosystem doesn't matter.
ECOSYSTEM_MARKERS: dict[str, Ecosystem] = {
    "mix.lock": Ecosystem.ELIXIR,
    "mix.exs": Ecosystem.ELIXIR,
    "Cargo.lock": Ecosystem.RUST,
    "Cargo.toml": Ecosystem.RUST,
    "package-lock.json": Ecosystem.NODE,
    "yarn.lock": Ecosystem.NODE,
    "pnpm-lock.yaml": Ecosystem.NODE,
    "go.sum": Ecosystem.GO,
    "go.mod": Ecosystem.GO,
    "requirements.txt": Ecosystem.PYTHON,
    "pyproject.toml": Ecosystem.PYTHON,
    "poetry.lock": Ecosystem.PYTHON,
    "uv.lock": Ecosystem.PYTHON,
}

# Non-python update commands are static. Python is resolved per-repo by
# _python_update_command so we pick the right tool for the lockfile present.
UPDATE_COMMANDS: dict[Ecosystem, str] = {
    Ecosystem.ELIXIR: "mix deps.update --all",
    Ecosystem.RUST: "cargo update",
    Ecosystem.NODE: "npm update",
    Ecosystem.GO: "go get -u ./...",
}

TEST_COMMANDS: dict[Ecosystem, str] = {
    Ecosystem.ELIXIR: "mix test",
    Ecosystem.RUST: "cargo test",
    Ecosystem.NODE: "npm test",
    Ecosystem.GO: "go test ./...",
    Ecosystem.PYTHON: "pytest",
}

OUTDATED_COMMANDS: dict[Ecosystem, str] = {
    Ecosystem.ELIXIR: "mix hex.outdated",
    Ecosystem.RUST: "cargo outdated",
    Ecosystem.NODE: "npm outdated",
    Ecosystem.GO: "go list -u -m all",
    Ecosystem.PYTHON: "pip list --outdated",
}


def detect_ecosystems(repo_path: str) -> list[Ecosystem]:
    """Detect which ecosystems are present in a repository by checking for marker files."""
    root = Path(repo_path)
    found: set[Ecosystem] = set()
    for filename, ecosystem in ECOSYSTEM_MARKERS.items():
        if (root / filename).exists():
            found.add(ecosystem)
    return sorted(found, key=lambda e: e.value)


def get_update_command(
    ecosystem: Ecosystem,
    repo_path: str = ".",
    deps: list[Dependency] | None = None,
) -> str:
    """Return the shell command to update deps for an ecosystem.

    For Python, the command depends on which lockfile is present in
    ``repo_path``. ``deps`` is consulted only for pyproject.toml-only repos,
    where the command upgrades each outdated package by name.
    """
    if ecosystem == Ecosystem.PYTHON:
        return _python_update_command(Path(repo_path), deps or [])
    return UPDATE_COMMANDS[ecosystem]


def _python_update_command(root: Path, deps: list[Dependency]) -> str:
    """Pick the right Python upgrade command for the repo's lockfile.

    Priority: uv.lock > poetry.lock > requirements.txt > pyproject-only.
    """
    if (root / "uv.lock").exists():
        return "uv sync --upgrade"
    if (root / "poetry.lock").exists():
        return "poetry update"
    if (root / "requirements.txt").exists():
        return "pip install --upgrade -r requirements.txt"
    if deps:
        pkgs = " ".join(d.name for d in deps)
        return f"pip install --upgrade {pkgs}"
    # No lockfile and nothing to upgrade -- a safe no-op that still answers
    # "what would you run?" without mutating the venv.
    return "pip list --outdated"


def get_test_command(ecosystem: Ecosystem) -> str:
    """Return the shell command to run tests for an ecosystem."""
    return TEST_COMMANDS[ecosystem]


def get_outdated_command(ecosystem: Ecosystem) -> str | None:
    """Return the command to list outdated deps, or None if unsupported."""
    return OUTDATED_COMMANDS.get(ecosystem)
