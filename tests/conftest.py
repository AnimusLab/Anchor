"""Shared pytest fixtures."""
import contextlib

import pytest


@pytest.fixture
def isolated_fs(tmp_path_factory, monkeypatch):
    """Replacement for Click's deprecated ``CliRunner.isolated_filesystem()``.

    Returns a context manager factory; each ``with isolated_fs():`` block runs in a
    fresh empty temporary directory. The original cwd is restored at test teardown.
    """

    @contextlib.contextmanager
    def _isolated():
        directory = tmp_path_factory.mktemp("fs")
        monkeypatch.chdir(directory)
        yield str(directory)

    return _isolated
