"""Tests for autoresearch data models."""

from autoresearch.models import (
    Direction,
    ExperimentConfig,
    ExperimentState,
    RunResult,
    Status,
)


def _config(**kwargs) -> ExperimentConfig:
    defaults = {
        "name": "test",
        "objective": "minimize loss",
        "metric_name": "loss",
        "direction": Direction.LOWER,
        "verify_command": "echo 'METRIC loss=1.0'",
    }
    defaults.update(kwargs)
    return ExperimentConfig(**defaults)


def _result(run: int, metric: float | None, status: Status = Status.KEEP) -> RunResult:
    return RunResult(run=run, metric=metric, status=status, description=f"run {run}")


class TestExperimentState:
    def test_is_better_lower(self):
        state = ExperimentState(config=_config(direction=Direction.LOWER))
        state.results = [_result(0, 1.0, Status.BASELINE)]
        state.best_metric = 1.0
        state.best_run = 0
        state.results.append(_result(1, 0.8))
        assert state.is_better

    def test_is_not_better_lower(self):
        state = ExperimentState(config=_config(direction=Direction.LOWER))
        state.results = [_result(0, 1.0, Status.BASELINE)]
        state.best_metric = 1.0
        state.best_run = 0
        state.results.append(_result(1, 1.5))
        assert not state.is_better

    def test_is_better_higher(self):
        state = ExperimentState(config=_config(direction=Direction.HIGHER))
        state.results = [_result(0, 50.0, Status.BASELINE)]
        state.best_metric = 50.0
        state.best_run = 0
        state.results.append(_result(1, 55.0))
        assert state.is_better

    def test_is_not_better_higher(self):
        state = ExperimentState(config=_config(direction=Direction.HIGHER))
        state.results = [_result(0, 50.0, Status.BASELINE)]
        state.best_metric = 50.0
        state.best_run = 0
        state.results.append(_result(1, 45.0))
        assert not state.is_better

    def test_is_better_none_metric(self):
        state = ExperimentState(config=_config())
        state.best_metric = 1.0
        state.results = [_result(0, None, Status.CRASH)]
        assert not state.is_better

    def test_is_better_no_best(self):
        state = ExperimentState(config=_config())
        state.results = [_result(0, 1.0)]
        assert not state.is_better

    def test_update_best_lower(self):
        state = ExperimentState(config=_config(direction=Direction.LOWER))
        state.results = [
            _result(0, 1.0, Status.BASELINE),
            _result(1, 0.8),
            _result(2, 0.9),
            _result(3, 0.5),
        ]
        state.update_best()
        assert state.best_metric == 0.5
        assert state.best_run == 3

    def test_update_best_higher(self):
        state = ExperimentState(config=_config(direction=Direction.HIGHER))
        state.results = [
            _result(0, 50.0, Status.BASELINE),
            _result(1, 55.0),
            _result(2, 60.0),
        ]
        state.update_best()
        assert state.best_metric == 60.0
        assert state.best_run == 2

    def test_update_best_skips_crashes(self):
        state = ExperimentState(config=_config(direction=Direction.LOWER))
        state.results = [
            _result(0, 1.0, Status.BASELINE),
            _result(1, None, Status.CRASH),
            _result(2, 0.5),
        ]
        state.update_best()
        assert state.best_metric == 0.5
        assert state.best_run == 2


class TestExperimentConfig:
    def test_defaults(self):
        cfg = _config()
        assert cfg.time_budget_seconds == 300
        assert cfg.guard_command is None
        assert cfg.mutable_files == []
        assert cfg.readonly_files == []

    def test_custom_values(self):
        cfg = _config(
            time_budget_seconds=60,
            guard_command="cargo test",
            mutable_files=["train.py"],
        )
        assert cfg.time_budget_seconds == 60
        assert cfg.guard_command == "cargo test"
        assert cfg.mutable_files == ["train.py"]
