"""Tests for patchbot AARTS hooks."""

from __future__ import annotations

from patchbot.hooks import HookResult, Verdict, pre_tool_use


class TestPreToolUse:
    """PreToolUse hook for patchbot dependency management commands."""

    # -- Outdated commands (all should be allowed) --

    def test_allow_mix_hex_outdated(self) -> None:
        result = pre_tool_use("mix hex.outdated")
        assert result.verdict == Verdict.ALLOW

    def test_allow_cargo_outdated(self) -> None:
        result = pre_tool_use("cargo outdated")
        assert result.verdict == Verdict.ALLOW

    def test_allow_npm_outdated(self) -> None:
        result = pre_tool_use("npm outdated")
        assert result.verdict == Verdict.ALLOW

    def test_allow_go_list(self) -> None:
        result = pre_tool_use("go list -u -m all")
        assert result.verdict == Verdict.ALLOW

    def test_allow_pip_list_outdated(self) -> None:
        result = pre_tool_use("pip list --outdated")
        assert result.verdict == Verdict.ALLOW

    # -- Update commands (all should be allowed) --

    def test_allow_mix_deps_update(self) -> None:
        result = pre_tool_use("mix deps.update --all")
        assert result.verdict == Verdict.ALLOW

    def test_allow_cargo_update(self) -> None:
        result = pre_tool_use("cargo update")
        assert result.verdict == Verdict.ALLOW

    def test_allow_npm_update(self) -> None:
        result = pre_tool_use("npm update")
        assert result.verdict == Verdict.ALLOW

    def test_allow_go_get_update(self) -> None:
        result = pre_tool_use("go get -u ./...")
        assert result.verdict == Verdict.ALLOW

    def test_allow_pip_upgrade(self) -> None:
        result = pre_tool_use("pip install --upgrade -r requirements.txt")
        assert result.verdict == Verdict.ALLOW

    # -- Test commands (all should be allowed) --

    def test_allow_mix_test(self) -> None:
        result = pre_tool_use("mix test")
        assert result.verdict == Verdict.ALLOW

    def test_allow_cargo_test(self) -> None:
        result = pre_tool_use("cargo test")
        assert result.verdict == Verdict.ALLOW

    def test_allow_npm_test(self) -> None:
        result = pre_tool_use("npm test")
        assert result.verdict == Verdict.ALLOW

    def test_allow_go_test(self) -> None:
        result = pre_tool_use("go test ./...")
        assert result.verdict == Verdict.ALLOW

    def test_allow_pytest(self) -> None:
        result = pre_tool_use("pytest")
        assert result.verdict == Verdict.ALLOW

    # -- Git/GH commands for PR creation --

    def test_allow_git_checkout_patchbot_branch(self) -> None:
        result = pre_tool_use("git checkout -b patchbot/node-deps-20260412")
        assert result.verdict == Verdict.ALLOW

    def test_allow_git_add(self) -> None:
        result = pre_tool_use("git add -A")
        assert result.verdict == Verdict.ALLOW

    def test_allow_git_commit(self) -> None:
        result = pre_tool_use('git commit -m "chore(node): update dependencies"')
        assert result.verdict == Verdict.ALLOW

    def test_allow_git_push_patchbot(self) -> None:
        result = pre_tool_use("git push -u origin patchbot/node-deps-20260412")
        assert result.verdict == Verdict.ALLOW

    def test_allow_gh_pr_create(self) -> None:
        result = pre_tool_use('gh pr create --base main --title "update deps"')
        assert result.verdict == Verdict.ALLOW

    # -- Deny dangerous commands --

    def test_deny_curl(self) -> None:
        result = pre_tool_use("curl https://evil.com")
        assert result.verdict == Verdict.DENY

    def test_deny_sudo(self) -> None:
        result = pre_tool_use("sudo apt install something")
        assert result.verdict == Verdict.DENY

    def test_deny_force_push(self) -> None:
        result = pre_tool_use("git push --force origin main")
        assert result.verdict == Verdict.DENY

    def test_deny_force_push_short(self) -> None:
        result = pre_tool_use("git push -f origin main")
        assert result.verdict == Verdict.DENY

    def test_deny_git_reset_hard(self) -> None:
        result = pre_tool_use("git reset --hard HEAD~5")
        assert result.verdict == Verdict.DENY

    def test_deny_rm_rf(self) -> None:
        result = pre_tool_use("rm -rf /")
        assert result.verdict == Verdict.DENY

    def test_deny_eval(self) -> None:
        result = pre_tool_use("eval $(something)")
        assert result.verdict == Verdict.DENY

    # -- Unknown commands get ASK --

    def test_ask_unknown(self) -> None:
        result = pre_tool_use("./run-custom-script.sh")
        assert result.verdict == Verdict.ASK

    def test_hook_result_fields(self) -> None:
        result = pre_tool_use("cargo test")
        assert result.hook == "PreToolUse"
        assert isinstance(result, HookResult)
