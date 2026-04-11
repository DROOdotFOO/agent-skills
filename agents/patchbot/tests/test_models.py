"""Tests for patchbot models."""

from patchbot.models import Dependency, Ecosystem, UpdatePlan, UpdateResult


def test_ecosystem_values():
    assert Ecosystem.ELIXIR.value == "elixir"
    assert Ecosystem.RUST.value == "rust"
    assert Ecosystem.NODE.value == "node"
    assert Ecosystem.GO.value == "go"
    assert Ecosystem.PYTHON.value == "python"


def test_dependency_minimal():
    dep = Dependency(name="phoenix", current_version="1.7.0", ecosystem=Ecosystem.ELIXIR)
    assert dep.name == "phoenix"
    assert dep.current_version == "1.7.0"
    assert dep.latest_version is None
    assert dep.ecosystem == Ecosystem.ELIXIR


def test_dependency_with_latest():
    dep = Dependency(
        name="serde",
        current_version="1.0.190",
        latest_version="1.0.200",
        ecosystem=Ecosystem.RUST,
    )
    assert dep.latest_version == "1.0.200"


def test_update_plan():
    deps = [
        Dependency(name="express", current_version="4.18.0", ecosystem=Ecosystem.NODE),
        Dependency(name="lodash", current_version="4.17.0", ecosystem=Ecosystem.NODE),
    ]
    plan = UpdatePlan(
        ecosystem=Ecosystem.NODE,
        dependencies=deps,
        update_command="npm update",
        test_command="npm test",
    )
    assert plan.ecosystem == Ecosystem.NODE
    assert len(plan.dependencies) == 2
    assert plan.update_command == "npm update"
    assert plan.test_command == "npm test"


def test_update_result_success():
    plan = UpdatePlan(
        ecosystem=Ecosystem.GO,
        dependencies=[],
        update_command="go get -u ./...",
        test_command="go test ./...",
    )
    result = UpdateResult(
        plan=plan, success=True, test_passed=True, pr_url="https://github.com/x/pulls/1"
    )
    assert result.success is True
    assert result.test_passed is True
    assert result.pr_url == "https://github.com/x/pulls/1"


def test_update_result_defaults():
    plan = UpdatePlan(
        ecosystem=Ecosystem.PYTHON,
        dependencies=[],
        update_command="pip install --upgrade -r requirements.txt",
        test_command="pytest",
    )
    result = UpdateResult(plan=plan, success=False, test_passed=False)
    assert result.pr_url is None
