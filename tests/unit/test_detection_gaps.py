"""Regression tests for detection gaps found in the Oct 2026 audit.
Known gaps are xfail (strict) so they flip to failures the moment they are fixed."""
import subprocess, sys
import pytest


def scan(tmp_path, code):
    (tmp_path / "a.py").write_text(code)
    r = subprocess.run([sys.executable, "-m", "anchor", "check", str(tmp_path)], capture_output=True, text=True)
    return r.stdout + r.stderr


@pytest.mark.xfail(reason="SEC-010 did not fire on exec(user_input) in 6.0.2; investigate scope/config", strict=False)
def test_exec_flagged(tmp_path):
    assert "SEC-010" in scan(tmp_path, "def run(user_input):\n    exec(user_input)\n")


@pytest.mark.xfail(reason="Layer 2 shell rule is scoped to call sites, not payload strings (6.0.2)", strict=False)
def test_guard_blocks_shell_payload():
    from anchor.guard import guard

    @guard(domain="finance")
    def f(x):
        return "ran"

    assert f({"cmd": "rm -rf /"}) != "ran"
