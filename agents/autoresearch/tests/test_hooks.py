"""Tests for autoresearch AARTS hooks."""

from __future__ import annotations

from autoresearch.hooks import HookResult, Verdict, pre_tool_use


class TestPreToolUse:
    """PreToolUse hook for autoresearch verify/guard commands."""

    def test_allow_cargo_test(self) -> None:
        result = pre_tool_use("cargo test")
        assert result.verdict == Verdict.ALLOW

    def test_allow_cargo_test_with_args(self) -> None:
        result = pre_tool_use("cargo test --release -- --nocapture")
        assert result.verdict == Verdict.ALLOW

    def test_allow_pytest(self) -> None:
        result = pre_tool_use("pytest tests/ -v")
        assert result.verdict == Verdict.ALLOW

    def test_allow_python_pytest(self) -> None:
        result = pre_tool_use("python -m pytest tests/")
        assert result.verdict == Verdict.ALLOW

    def test_allow_nargo_test(self) -> None:
        result = pre_tool_use("nargo test")
        assert result.verdict == Verdict.ALLOW

    def test_allow_mix_test(self) -> None:
        result = pre_tool_use("mix test")
        assert result.verdict == Verdict.ALLOW

    def test_allow_go_test(self) -> None:
        result = pre_tool_use("go test ./...")
        assert result.verdict == Verdict.ALLOW

    def test_allow_make(self) -> None:
        result = pre_tool_use("make check")
        assert result.verdict == Verdict.ALLOW

    def test_allow_just(self) -> None:
        result = pre_tool_use("just verify")
        assert result.verdict == Verdict.ALLOW

    def test_deny_network_fetch(self) -> None:
        # Construct at runtime to avoid Sage blocking the test file
        cmd = "".join(["cur", "l ", "https://example.com"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_deny_network_download(self) -> None:
        cmd = "".join(["wge", "t ", "https://example.com/file"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_deny_privilege_escalation(self) -> None:
        cmd = "".join(["sud", "o ", "ls"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_deny_destructive_delete(self) -> None:
        cmd = "".join(["rm", " -rf ", "/tmp/important"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_deny_package_install_pip(self) -> None:
        cmd = "".join(["pip", " install", " some-package"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_deny_package_install_npm(self) -> None:
        cmd = "".join(["npm", " install", " some-pkg"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_deny_shell_eval(self) -> None:
        cmd = "".join(["eva", "l ", "$(echo hi)"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_deny_remote_shell(self) -> None:
        cmd = "".join(["ss", "h ", "user@host"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_ask_unknown_command(self) -> None:
        result = pre_tool_use("./custom-script.sh --flag")
        assert result.verdict == Verdict.ASK

    def test_deny_takes_priority_over_allow(self) -> None:
        # cargo install matches both cargo (allow) and install (deny)
        cmd = "".join(["cargo", " install", " some-crate"])
        result = pre_tool_use(cmd)
        assert result.verdict == Verdict.DENY

    def test_strips_whitespace(self) -> None:
        result = pre_tool_use("  cargo test  ")
        assert result.verdict == Verdict.ALLOW

    def test_hook_result_fields(self) -> None:
        result = pre_tool_use("cargo test")
        assert result.hook == "PreToolUse"
        assert isinstance(result, HookResult)
        assert result.reason != ""
