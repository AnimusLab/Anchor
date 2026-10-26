import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

import anchor
from anchor.cli import cli

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
PKG_ROOT = str(Path(anchor.__file__).resolve().parent.parent)


def _git(repo, *args, env_extra=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    env["PYTHONPATH"] = PKG_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env.update(env_extra or {})
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=env)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _init(*args):
    result = CliRunner().invoke(cli, ["init", "--no-prompt", *args])
    assert result.exit_code == 0, result.output
    return result.output


# --- private key protection ------------------------------------------------------

def test_private_key_is_gitignored_by_default(repo):
    out = _init()
    assert ".anchor/keys/ed25519_private.pem" in (repo / ".gitignore").read_text().splitlines()
    assert ".anchor/cache/" not in (repo / ".gitignore").read_text()  # cache entry is still opt-in
    assert "private key to .gitignore" in out
    _git(repo, "add", "-A")
    staged = _git(repo, "diff", "--cached", "--name-only").stdout
    assert "ed25519_private.pem" not in staged


def test_gitignore_flag_adds_cache_too_and_is_idempotent(repo):
    _init("--gitignore")
    _init("--gitignore")
    lines = (repo / ".gitignore").read_text().splitlines()
    assert lines.count(".anchor/cache/") == 1
    assert lines.count(".anchor/keys/ed25519_private.pem") == 1


def test_existing_gitignore_without_trailing_newline_is_preserved(repo):
    (repo / ".gitignore").write_text("node_modules")
    _init()
    assert (repo / ".gitignore").read_text().splitlines()[0] == "node_modules"


def test_outside_a_git_repo_gitignore_is_not_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init()
    assert not (tmp_path / ".gitignore").exists()


# --- hook --------------------------------------------------------------------------

def test_hook_uses_the_installing_interpreter(repo):
    _init("--hook")
    hook = (repo / ".git/hooks/pre-commit").read_text()
    assert sys.executable in hook
    assert os.access(repo / ".git/hooks/pre-commit", os.X_OK)


def test_hook_blocks_bad_staged_file_of_any_language(repo):
    _init("--hook")
    (repo / "bad.js").write_text("function f(x){ eval(x); }\n")
    _git(repo, "add", "bad.js")
    result = _git(repo, "commit", "-m", "x")
    assert result.returncode != 0
    assert "SEC-010" in result.stdout + result.stderr


def test_hook_only_checks_staged_files(repo):
    _init("--hook")
    (repo / "bad.py").write_text("eval(x)\n")          # never staged
    (repo / "good.py").write_text("x = 1\n")
    _git(repo, "add", "good.py")
    result = _git(repo, "commit", "-m", "x")
    assert result.returncode == 0, result.stdout + result.stderr


def test_hook_skips_when_nothing_is_staged(repo):
    _init("--hook")
    result = _git(repo, "commit", "--allow-empty", "-m", "empty")
    assert result.returncode == 0


def test_hook_backs_up_an_existing_hook(repo):
    hooks = repo / ".git/hooks"
    hooks.mkdir(exist_ok=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\necho mine\n")
    _init("--hook")
    assert "echo mine" in (hooks / "pre-commit.bak").read_text()


# --- honest registry / hub messages -----------------------------------------------

def test_registry_message_does_not_claim_the_key_was_queued(repo):
    # CliRunner stdin is not a tty, so this exercises the non-interactive path.
    # The interactive "y" answer is covered by test_registry_yes_through_a_pty.
    result = CliRunner().invoke(cli, ["init"], input="n\nn\ny\n")
    assert "queued" not in result.output and "REGISTERED" not in result.output
    assert "NOT SENT" in result.output or "LOCAL ONLY" in result.output


def test_hub_key_is_not_echoed_or_claimed_as_provisioned(repo):
    out = _init("--hub-key", "hub_live_ABCDEFGHIJKLMNOP", "--project-key", "proj_xyz")
    assert "hub_live" not in out
    assert "Provisioned" not in out
    assert "not validated" in out


@pytest.mark.skipif(sys.platform == "win32", reason="needs a pty")
def test_registry_yes_through_a_pty(repo):
    import pty
    import select
    import time

    pid, fd = pty.fork()
    if pid == 0:  # child
        os.environ["PYTHONPATH"] = PKG_ROOT
        os.execv(sys.executable, [sys.executable, "-m", "anchor", "init"])
    out = b""
    deadline = time.time() + 30
    while time.time() < deadline:
        ready, _, _ = select.select([fd], [], [], 1)
        if not ready:
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
        if chunk.rstrip().endswith(b":") or b"[y/N]" in chunk or b"[Y/n]" in chunk:
            os.write(fd, b"y\n")
    os.waitpid(pid, 0)
    text = out.decode(errors="replace")
    assert "Register public identity" in text
    assert "NOT SENT" in text
    assert "queued" not in text and "[REGISTERED]" not in text
