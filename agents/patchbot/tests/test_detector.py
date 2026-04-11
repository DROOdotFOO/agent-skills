"""Tests for patchbot ecosystem detection."""

import tempfile
from pathlib import Path

from patchbot.detector import (
    detect_ecosystems,
    get_outdated_command,
    get_test_command,
    get_update_command,
)
from patchbot.models import Ecosystem


def test_detect_elixir():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "mix.exs").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.ELIXIR in result


def test_detect_rust():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Cargo.toml").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.RUST in result


def test_detect_node_npm():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "package-lock.json").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.NODE in result


def test_detect_node_yarn():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "yarn.lock").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.NODE in result


def test_detect_node_pnpm():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "pnpm-lock.yaml").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.NODE in result


def test_detect_go():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "go.mod").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.GO in result


def test_detect_python_requirements():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "requirements.txt").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.PYTHON in result


def test_detect_python_pyproject():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "pyproject.toml").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.PYTHON in result


def test_detect_python_uv():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "uv.lock").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.PYTHON in result


def test_detect_multiple():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Cargo.toml").touch()
        (Path(tmp) / "package-lock.json").touch()
        (Path(tmp) / "go.mod").touch()
        result = detect_ecosystems(tmp)
        assert Ecosystem.RUST in result
        assert Ecosystem.NODE in result
        assert Ecosystem.GO in result
        assert len(result) == 3


def test_detect_empty_dir():
    with tempfile.TemporaryDirectory() as tmp:
        result = detect_ecosystems(tmp)
        assert result == []


def test_detect_no_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "mix.exs").touch()
        (Path(tmp) / "mix.lock").touch()
        result = detect_ecosystems(tmp)
        assert result.count(Ecosystem.ELIXIR) == 1


def test_get_update_commands():
    assert get_update_command(Ecosystem.ELIXIR) == "mix deps.update --all"
    assert get_update_command(Ecosystem.RUST) == "cargo update"
    assert get_update_command(Ecosystem.NODE) == "npm update"
    assert get_update_command(Ecosystem.GO) == "go get -u ./..."
    assert "pip" in get_update_command(Ecosystem.PYTHON)


def test_get_test_commands():
    assert get_test_command(Ecosystem.ELIXIR) == "mix test"
    assert get_test_command(Ecosystem.RUST) == "cargo test"
    assert get_test_command(Ecosystem.NODE) == "npm test"
    assert get_test_command(Ecosystem.GO) == "go test ./..."
    assert get_test_command(Ecosystem.PYTHON) == "pytest"


def test_get_outdated_commands():
    assert get_outdated_command(Ecosystem.ELIXIR) == "mix hex.outdated"
    assert get_outdated_command(Ecosystem.RUST) == "cargo outdated"
    assert get_outdated_command(Ecosystem.NODE) == "npm outdated"
    assert "go list" in get_outdated_command(Ecosystem.GO)
    assert "pip" in get_outdated_command(Ecosystem.PYTHON)


def test_results_are_sorted():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Cargo.toml").touch()
        (Path(tmp) / "mix.exs").touch()
        (Path(tmp) / "go.mod").touch()
        result = detect_ecosystems(tmp)
        values = [e.value for e in result]
        assert values == sorted(values)
