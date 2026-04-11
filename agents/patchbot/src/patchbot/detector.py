"""Detect ecosystems present in a repository."""

from pathlib import Path

from patchbot.models import Ecosystem

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

UPDATE_COMMANDS: dict[Ecosystem, str] = {
    Ecosystem.ELIXIR: "mix deps.update --all",
    Ecosystem.RUST: "cargo update",
    Ecosystem.NODE: "npm update",
    Ecosystem.GO: "go get -u ./...",
    Ecosystem.PYTHON: "pip install --upgrade -r requirements.txt",
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


def get_update_command(ecosystem: Ecosystem) -> str:
    """Return the shell command to update deps for an ecosystem."""
    return UPDATE_COMMANDS[ecosystem]


def get_test_command(ecosystem: Ecosystem) -> str:
    """Return the shell command to run tests for an ecosystem."""
    return TEST_COMMANDS[ecosystem]


def get_outdated_command(ecosystem: Ecosystem) -> str | None:
    """Return the command to list outdated deps, or None if unsupported."""
    return OUTDATED_COMMANDS.get(ecosystem)
