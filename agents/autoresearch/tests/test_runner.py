"""Tests for experiment runner."""

from autoresearch.agent import parse_agent_response
from autoresearch.runner import extract_metrics


class TestExtractMetrics:
    def test_single_metric(self):
        output = "Training...\nMETRIC loss=0.523\nDone."
        metrics = extract_metrics(output, r"METRIC\s+(\S+)=(\S+)")
        assert metrics == {"loss": 0.523}

    def test_multiple_metrics(self):
        output = "METRIC loss=0.5\nMETRIC accuracy=0.95\nMETRIC time=12.3"
        metrics = extract_metrics(output, r"METRIC\s+(\S+)=(\S+)")
        assert metrics == {"loss": 0.5, "accuracy": 0.95, "time": 12.3}

    def test_no_metrics(self):
        output = "No metrics here\njust regular output"
        metrics = extract_metrics(output, r"METRIC\s+(\S+)=(\S+)")
        assert metrics == {}

    def test_invalid_value_skipped(self):
        output = "METRIC loss=notanumber\nMETRIC accuracy=0.9"
        metrics = extract_metrics(output, r"METRIC\s+(\S+)=(\S+)")
        assert metrics == {"accuracy": 0.9}

    def test_custom_pattern(self):
        output = "val_bpb: 1.234\npeak_vram_mb: 8192"
        pattern = r"(\w+):\s+(\d+\.?\d*)"
        metrics = extract_metrics(output, pattern)
        assert metrics["val_bpb"] == 1.234
        assert metrics["peak_vram_mb"] == 8192.0

    def test_negative_values(self):
        output = "METRIC delta=-0.05"
        metrics = extract_metrics(output, r"METRIC\s+(\S+)=(\S+)")
        assert metrics == {"delta": -0.05}


class TestParseAgentResponse:
    def test_basic_response(self):
        text = """DESCRIPTION: Increase learning rate from 0.001 to 0.01
FILE: train.py
```
lr = 0.01
model.train()
```"""
        desc, files = parse_agent_response(text)
        assert desc == "Increase learning rate from 0.001 to 0.01"
        assert "train.py" in files
        assert "lr = 0.01" in files["train.py"]

    def test_multiple_files(self):
        text = """DESCRIPTION: Refactor optimizer config
FILE: train.py
```
import torch
```
FILE: config.py
```
LR = 0.01
```"""
        desc, files = parse_agent_response(text)
        assert len(files) == 2
        assert "train.py" in files
        assert "config.py" in files

    def test_no_description_fallback(self):
        text = """FILE: train.py
```
x = 1
```"""
        desc, files = parse_agent_response(text)
        assert desc == "Agent-proposed change"
        assert "train.py" in files

    def test_empty_response(self):
        desc, files = parse_agent_response("")
        assert desc == "Agent-proposed change"
        assert files == {}

    def test_language_tag_in_code_fence(self):
        text = """DESCRIPTION: Fix bug
FILE: script.py
```python
print("hello")
```"""
        desc, files = parse_agent_response(text)
        # The ```python line starts with ```, so it triggers the code block
        assert "script.py" in files
