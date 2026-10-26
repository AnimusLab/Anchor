import json
import os

import pytest
from click.testing import CliRunner

from anchor.cli import cli
from anchor.scanner.pragmas import filter_violations, parse_pragma, suppressions

SECRET = 'OPENAI_API_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF"'


def _check(path, *extra):
    result = CliRunner().invoke(cli, ["check", str(path), "--format", "json", *extra])
    data = json.loads(result.output[result.output.index("{"):])
    return result.exit_code, sorted((v["aggregated_rule_ids"], v["line"]) for v in data["violations"])


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body)
    return p


@pytest.fixture(autouse=True)
def _in_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


# --- parsing -----------------------------------------------------------------

def test_parse_trailing_pragma_with_ids():
    ids, comment_only = parse_pragma("os.system(x)  # anchor: ignore SEC-007 RI-08 -- reviewed")
    assert ids == {"SEC-007", "RI-08"} and not comment_only


def test_parse_blanket_pragma_with_reason_only():
    ids, comment_only = parse_pragma("# anchor: ignore -- test fixture for SEC-007 detection")
    assert ids == frozenset() and comment_only  # ids after `--` are prose, not scope


def test_suppression_targets():
    lines = ["a  # anchor: ignore SEC-007", "# anchor: ignore", "b", "c"]
    sup = suppressions(lines)
    assert sup[1] == [frozenset({"SEC-007"})]  # trailing -> own line only
    assert sup[3] == [frozenset()]             # comment-only -> next line only
    assert 2 not in sup and 4 not in sup


# --- end to end ----------------------------------------------------------------

def test_pragma_no_longer_hides_other_rules_on_next_line(tmp_path):
    p = _write(tmp_path, "a.py", 'import os\nos.system("ls " + x)  # anchor: ignore SEC-007\neval(y)\n' + SECRET + "\n")
    code, found = _check(p)
    assert ("SEC-007", 2) not in found           # the reviewed line stays suppressed
    assert ("SEC-010", 3) in found               # eval on the next line is reported again
    assert ("SEC-002", 4) in found
    assert code == 1


def test_pragma_for_a_different_rule_does_not_suppress(tmp_path):
    p = _write(tmp_path, "a.py", "eval(y)  # anchor: ignore SEC-007\n")
    assert ("SEC-010", 1) in _check(p)[1]


def test_pragma_for_matching_rule_suppresses_same_line(tmp_path):
    p = _write(tmp_path, "a.py", "eval(y)  # anchor: ignore SEC-010\n")
    assert _check(p) == (0, [])


def test_comment_only_pragma_covers_exactly_the_next_line(tmp_path):
    p = _write(tmp_path, "a.py", "# anchor: ignore -- reviewed\neval(a)\neval(b)\n")
    assert _check(p)[1] == [("SEC-010", 3)]


def test_blanket_trailing_pragma_suppresses_every_rule_on_its_line(tmp_path):
    p = _write(tmp_path, "a.py", SECRET + "  # anchor: ignore -- rotated key\n")
    assert _check(p) == (0, [])


def test_files_without_pragmas_are_unchanged(tmp_path):
    p = _write(tmp_path, "a.py", "import os\nos.system(x)\neval(y)\n")
    assert [r for r, _ in _check(p)[1]] == ["SEC-007", "SEC-010"]


def test_directory_scan_reports_original_paths_and_code(tmp_path):
    sub = tmp_path / "pkg"
    sub.mkdir()
    _write(sub, "m.py", "import os\nx = 1\n    eval(user)\n")
    _write(tmp_path, "ok.py", "y = 1  # anchor: ignore\n")
    result = CliRunner().invoke(cli, ["check", ".", "--format", "json"])
    data = json.loads(result.output[result.output.index("{"):])
    hit = [v for v in data["violations"] if v["aggregated_rule_ids"] == "SEC-010"][0]
    assert hit["file"] == os.path.realpath(sub / "m.py") or hit["file"] == str(sub / "m.py")
    assert hit["line_content"] == "eval(user)"
    assert not os.path.exists(tmp_path / "anchor-pragma-")  # scratch copy cleaned up


def test_legacy_rule_ids_in_existing_pragmas_still_apply(tmp_path):
    p = _write(tmp_path, "a.py", "import os\nos.system(c)  # anchor: ignore ANC-018\neval(x)  # anchor: ignore ANC-030\n")
    assert _check(p) == (0, [])
    q = _write(tmp_path, "b.py", "import os\nos.system(c)  # anchor: ignore ANC-030\n")
    assert _check(q)[1] == [("SEC-007", 2)]  # an alias only covers its own rule


def test_legacy_env_var_restores_engine_behaviour(tmp_path, monkeypatch):
    p = _write(tmp_path, "a.py", "import os\nos.system(c)  # anchor: ignore SEC-007\neval(y)\n")
    assert ("SEC-010", 3) in _check(p)[1]
    monkeypatch.setenv("ANCHOR_LEGACY_PRAGMAS", "1")
    assert _check(p) == (0, [])  # engine semantics: the next line is hidden too


def test_filter_violations_ignores_unreadable_files():
    v = {"file": "/nonexistent/x.py", "line": 1, "aggregated_rule_ids": "SEC-010"}
    assert filter_violations([v]) == [v]
