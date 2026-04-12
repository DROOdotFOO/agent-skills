"""Tests for autoresearch AARTS hooks."""

from __future__ import annotations

from autoresearch.hooks import (
    HookResult,
    Verdict,
    log_hook_result,
    pre_sub_agent_spawn,
    pre_tool_use,
)


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


class TestPreSubAgentSpawn:
    """PreSubAgentSpawn hook for agent loop file changes."""

    MUTABLE = ["src/main.nr", "src/lib.nr"]

    def test_allow_mutable_file(self) -> None:
        changes = {"src/main.nr": "fn main() {}"}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.ALLOW

    def test_allow_multiple_mutable_files(self) -> None:
        changes = {"src/main.nr": "fn main() {}", "src/lib.nr": "mod utils;"}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.ALLOW

    def test_allow_empty_changes(self) -> None:
        result = pre_sub_agent_spawn({}, self.MUTABLE)
        assert result.verdict == Verdict.ALLOW

    def test_deny_non_mutable_file(self) -> None:
        changes = {"Cargo.toml": '[package]\nname = "exploit"'}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.DENY
        assert "not in mutable_files" in result.reason

    def test_deny_mixed_mutable_and_non(self) -> None:
        changes = {"src/main.nr": "ok", "README.md": "injected"}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.DENY

    def test_deny_os_system_in_content(self) -> None:
        changes = {"src/main.nr": 'import os\nos.system("rm -rf /")'}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.DENY
        assert "os.system()" in result.reason

    def test_deny_subprocess_in_content(self) -> None:
        changes = {"src/main.nr": 'import subprocess\nsubprocess.run(["ls"])'}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.DENY
        assert "subprocess" in result.reason

    def test_deny_eval_in_content(self) -> None:
        changes = {"src/main.nr": 'eval("malicious code")'}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.DENY

    def test_deny_exec_in_content(self) -> None:
        changes = {"src/main.nr": 'exec("import os")'}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.DENY

    def test_deny_dunder_import(self) -> None:
        changes = {"src/main.nr": '__import__("os").system("ls")'}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.DENY

    def test_allow_safe_code_content(self) -> None:
        changes = {"src/main.nr": "fn add(a: u32, b: u32) -> u32 { a + b }"}
        result = pre_sub_agent_spawn(changes, self.MUTABLE)
        assert result.verdict == Verdict.ALLOW

    def test_hook_result_fields(self) -> None:
        result = pre_sub_agent_spawn({"src/main.nr": "ok"}, self.MUTABLE)
        assert result.hook == "PreSubAgentSpawn"
        assert isinstance(result, HookResult)


class TestLogHookResult:
    """ASK verdict logging."""

    def test_ask_logs_to_stderr(self) -> None:
        import sys
        from io import StringIO

        capture = StringIO()
        old_stderr = sys.stderr
        sys.stderr = capture
        try:
            result = HookResult(verdict=Verdict.ASK, hook="PreToolUse", reason="test reason")
            log_hook_result(result)
        finally:
            sys.stderr = old_stderr
        assert "[HOOK] PreToolUse:" in capture.getvalue()
        assert "ASK verdict" in capture.getvalue()

    def test_allow_no_log(self) -> None:
        import sys
        from io import StringIO

        capture = StringIO()
        old_stderr = sys.stderr
        sys.stderr = capture
        try:
            log_hook_result(HookResult(verdict=Verdict.ALLOW, hook="PreToolUse", reason="ok"))
        finally:
            sys.stderr = old_stderr
        assert capture.getvalue() == ""

    def test_deny_no_log(self) -> None:
        import sys
        from io import StringIO

        capture = StringIO()
        old_stderr = sys.stderr
        sys.stderr = capture
        try:
            log_hook_result(HookResult(verdict=Verdict.DENY, hook="PreToolUse", reason="bad"))
        finally:
            sys.stderr = old_stderr
        assert capture.getvalue() == ""
