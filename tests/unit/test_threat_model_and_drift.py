import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from anchor.cli import _packaged_governance_dir, cli


def _runner():
    try:
        return CliRunner(mix_stderr=False)  # click < 8.2
    except TypeError:
        return CliRunner()                  # click >= 8.2 always keeps stdout/stderr separate


@pytest.fixture(autouse=True)
def _in_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANCHOR_REQUIRE_VERIFIED_GOVERNANCE", raising=False)


@pytest.fixture
def threat_model(tmp_path):
    p = tmp_path / "tm.md"
    p.write_text("| ID | Risk |\n| RI-24 | Unauthorized data access |\n| AI-20 | Hallucination |\n| RI-99 | made up |\n")
    return p


# --- -c / --context ------------------------------------------------------------------

def test_threat_model_does_not_claim_enforcement(tmp_path, threat_model):
    (tmp_path / "a.py").write_text("eval(x)\n")
    result = _runner().invoke(cli, ["check", "a.py", "-c", str(threat_model)])
    combined = result.stdout + result.stderr
    assert "Activated dynamic enforcement" not in combined
    assert "Informational only" in result.stderr
    assert "[DEBUG]" not in combined


def test_threat_model_does_not_change_findings(tmp_path, threat_model):
    (tmp_path / "a.py").write_text("import os\nos.system(x)\neval(y)\n")
    plain = _runner().invoke(cli, ["check", "a.py", "--format", "json"])
    with_tm = _runner().invoke(cli, ["check", "a.py", "--format", "json", "-c", str(threat_model)])
    assert json.loads(plain.stdout)["violations"] == json.loads(with_tm.stdout)["violations"]


def test_json_stdout_stays_parseable_with_context(tmp_path, threat_model):
    (tmp_path / "a.py").write_text("x = 1\n")
    result = _runner().invoke(cli, ["check", "a.py", "--format", "json", "-c", str(threat_model)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["is_compliant"] is True  # no banner in front of the JSON


def test_missing_threat_model_is_an_error(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    result = _runner().invoke(cli, ["check", "a.py", "-c", "nope.md"])
    assert result.exit_code == 2
    assert "not found" in result.stderr


# --- local .anchor drift ----------------------------------------------------------------

def _init():
    assert _runner().invoke(cli, ["init", "--no-prompt"]).exit_code == 0


def test_clean_init_reports_no_drift(tmp_path):
    _init()
    (tmp_path / "a.py").write_text("x = 1\n")
    result = _runner().invoke(cli, ["check", "a.py", "--format", "json"])
    assert "governance_drift" not in json.loads(result.stdout)
    human = _runner().invoke(cli, ["check", "a.py"]).stdout
    assert "LOCAL RULE FILES MODIFIED" not in human


def test_edited_local_catalog_is_reported(tmp_path):
    _init()
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / ".anchor/mitigation.anchor").write_text("# emptied\n")
    data = json.loads(_runner().invoke(cli, ["check", "a.py", "--format", "json"]).stdout)
    assert data["governance_drift"] == [".anchor/mitigation.anchor"]
    human = _runner().invoke(cli, ["check", "a.py"]).stdout
    assert "LOCAL RULE FILES MODIFIED" in human and "anchor sync --restore" in human


def test_edited_lock_is_reported(tmp_path):
    _init()
    (tmp_path / "a.py").write_text("x = 1\n")
    lock = tmp_path / ".anchor/GOVERNANCE.lock"
    lock.write_text(lock.read_text() + "tampered\n")
    data = json.loads(_runner().invoke(cli, ["check", "a.py", "--format", "json"]).stdout)
    assert ".anchor/GOVERNANCE.lock" in data["governance_drift"]


def test_drift_fails_when_verified_governance_is_required(tmp_path, monkeypatch):
    _init()
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / ".anchor/mitigation.anchor").write_text("# emptied\n")
    monkeypatch.setenv("ANCHOR_REQUIRE_VERIFIED_GOVERNANCE", "1")
    assert _runner().invoke(cli, ["check", "a.py", "--format", "json"]).exit_code == 2
    assert _runner().invoke(cli, ["check", "a.py"]).exit_code == 2


def test_sync_restore_clears_the_drift(tmp_path):
    _init()
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / ".anchor/mitigation.anchor").write_text("# emptied\n")
    assert _runner().invoke(cli, ["sync", "--restore"]).exit_code == 0
    data = json.loads(_runner().invoke(cli, ["check", "a.py", "--format", "json"]).stdout)
    assert "governance_drift" not in data
    assert (tmp_path / ".anchor/mitigation.anchor").read_bytes() == (_packaged_governance_dir() / "mitigation.anchor").read_bytes()


def test_scanning_without_a_local_anchor_dir_has_no_drift(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    data = json.loads(_runner().invoke(cli, ["check", "a.py", "--format", "json"]).stdout)
    assert "governance_drift" not in data
