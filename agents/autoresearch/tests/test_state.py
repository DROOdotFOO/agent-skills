"""Tests for JSONL state management."""

from pathlib import Path

from autoresearch.models import Direction, ExperimentConfig, RunResult, Status
from autoresearch.state import format_results_table, load_state, save_config, save_result


def _config(**kwargs) -> ExperimentConfig:
    defaults = {
        "name": "test",
        "objective": "minimize loss",
        "metric_name": "loss",
        "direction": Direction.LOWER,
        "verify_command": "echo test",
    }
    defaults.update(kwargs)
    return ExperimentConfig(**defaults)


class TestSaveAndLoad:
    def test_roundtrip_config(self, tmp_path: Path):
        path = tmp_path / "state.jsonl"
        cfg = _config(name="roundtrip", mutable_files=["train.py"])
        save_config(path, cfg)
        state = load_state(path)
        assert state is not None
        assert state.config.name == "roundtrip"
        assert state.config.mutable_files == ["train.py"]
        assert state.results == []

    def test_roundtrip_with_results(self, tmp_path: Path):
        path = tmp_path / "state.jsonl"
        save_config(path, _config())
        save_result(
            path, RunResult(run=0, metric=1.0, status=Status.BASELINE, description="baseline")
        )
        save_result(path, RunResult(run=1, metric=0.8, status=Status.KEEP, description="improved"))
        save_result(path, RunResult(run=2, metric=0.9, status=Status.DISCARD, description="worse"))

        state = load_state(path)
        assert state is not None
        assert len(state.results) == 3
        assert state.results[0].status == Status.BASELINE
        assert state.results[1].status == Status.KEEP
        assert state.best_metric == 0.8
        assert state.best_run == 1

    def test_load_missing_file(self, tmp_path: Path):
        assert load_state(tmp_path / "missing.jsonl") is None

    def test_load_empty_file(self, tmp_path: Path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        assert load_state(path) is None

    def test_new_config_resets_results(self, tmp_path: Path):
        path = tmp_path / "state.jsonl"
        save_config(path, _config(name="first"))
        save_result(path, RunResult(run=0, metric=1.0, status=Status.BASELINE))
        save_config(path, _config(name="second"))

        state = load_state(path)
        assert state.config.name == "second"
        assert state.results == []

    def test_malformed_lines_skipped(self, tmp_path: Path):
        path = tmp_path / "state.jsonl"
        save_config(path, _config())
        with path.open("a") as f:
            f.write("not json\n")
            f.write("{}\n")  # Missing type field
        save_result(path, RunResult(run=0, metric=1.0, status=Status.BASELINE))

        state = load_state(path)
        assert len(state.results) == 1


class TestFormatResultsTable:
    def test_empty_results(self, tmp_path: Path):
        from autoresearch.models import ExperimentState

        state = ExperimentState(config=_config(name="empty"))
        table = format_results_table(state)
        assert "empty" in table
        assert "no results yet" in table

    def test_with_results(self, tmp_path: Path):
        from autoresearch.models import ExperimentState

        state = ExperimentState(config=_config(name="test"))
        state.results = [
            RunResult(run=0, metric=1.0, status=Status.BASELINE, description="baseline"),
            RunResult(run=1, metric=0.8, status=Status.KEEP, description="improved"),
        ]
        state.update_best()
        table = format_results_table(state)
        assert "baseline" in table
        assert "improved" in table
        assert "0.8" in table
