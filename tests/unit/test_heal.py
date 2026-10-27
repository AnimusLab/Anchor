import json

import pytest
from click.testing import CliRunner

from anchor.cli import cli
from anchor.core.healer import suggest_fix


@pytest.fixture(autouse=True)
def _in_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _violations(path):
    result = CliRunner().invoke(cli, ["check", str(path), "--format", "json"])
    return json.loads(result.output[result.output.index("{"):])["violations"]


def test_heal_scans_the_given_path_not_the_last_report(tmp_path):
    (tmp_path / "other.py").write_text("import os\nos.system(a)\n")
    (tmp_path / "target.py").write_text("eval(x)\n")
    CliRunner().invoke(cli, ["check", "other.py"])          # leaves a report about other.py
    out = CliRunner().invoke(cli, ["heal", "target.py"]).output
    assert "target.py:1" in out
    assert "other.py" not in out


def test_heal_without_paths_uses_last_report(tmp_path):
    (tmp_path / "a.py").write_text("eval(x)\n")
    CliRunner().invoke(cli, ["check", "a.py"])
    out = CliRunner().invoke(cli, ["heal"]).output
    assert "a.py:1" in out and "last `anchor check` run" in out


def test_heal_missing_path_exits_2():
    assert CliRunner().invoke(cli, ["heal", "nope.py"]).exit_code == 2


def test_suppression_requires_explicit_flag(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("import os\nos.system(cmd)\n")
    before = p.read_text()

    out = CliRunner().invoke(cli, ["heal", "--apply", "a.py"]).output
    assert p.read_text() == before                       # nothing silently suppressed
    assert "--suppress" in out and "Applied 0" in out

    out = CliRunner().invoke(cli, ["heal", "--apply", "--suppress", "a.py"]).output
    assert "# anchor: ignore SEC-007" in p.read_text()
    assert "Applied 1" in out


def test_suppression_pragma_no_longer_hides_neighbouring_findings(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("import os\nos.system(cmd)\neval(user_input)\n")
    CliRunner().invoke(cli, ["heal", "--apply", "--suppress", "a.py"])
    assert [v["aggregated_rule_ids"] for v in _violations(p)] == ["SEC-010"]


def test_real_fix_is_applied_without_suppress(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("import requests\nrequests.get(url, verify=False)\n")
    CliRunner().invoke(cli, ["heal", "--apply", "a.py"])
    assert "verify=True" in p.read_text()
    assert _violations(p) == []


def test_secret_fix_keeps_the_variable_name(tmp_path):
    p = tmp_path / "a.py"
    key = "sk-" + "proj-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF"
    p.write_text(f'import os\nOPENAI_API_KEY = "{key}"\n')
    CliRunner().invoke(cli, ["heal", "--apply", "a.py"])
    assert p.read_text().splitlines()[1] == 'OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")'


def test_suggest_fix_marks_suppressions(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("import os\nos.system(cmd)\nrequests.get(u, verify=False)\n")
    suppress = suggest_fix({"id": "SEC-007", "file": str(f), "line": 2, "message": ""})
    real_fix = suggest_fix({"id": "SEC-024", "file": str(f), "line": 3, "message": ""})
    assert suppress.auto_fixable and suppress.suppression
    assert real_fix.auto_fixable and not real_fix.suppression
