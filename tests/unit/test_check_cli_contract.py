"""`anchor check` CLI contract: exit codes and --format must do what --help says.

Regression tests: in 6.0.6 `check` exited 0 even with violations (an
unreachable ``sys.exit(1)``), and ``--format json|markdown`` was accepted but
silently ignored, so CI gates could never fail and output could not be parsed.
"""
import json
from pathlib import Path

from click.testing import CliRunner

import anchor.cli as cli_mod

BAD = 'import os\ndef run(u):\n    eval(u)\n    os.system("rm -rf " + u)\n'


def _verified(monkeypatch):
    monkeypatch.setattr(cli_mod, "_governance_status", lambda: (True, ""))


def test_violations_exit_nonzero(monkeypatch):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.py").write_text(BAD)
        r = runner.invoke(cli_mod.cli, ["check", "."])
        assert r.exit_code == 1, r.output
        assert "VIOLATIONS FOUND" in r.output


def test_clean_tree_exits_zero(monkeypatch):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("ok.py").write_text("x = 1\n")
        assert runner.invoke(cli_mod.cli, ["check", "."]).exit_code == 0


def test_format_json_is_pure_json_and_exit_code_tracks_findings(monkeypatch):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.py").write_text(BAD)
        r = runner.invoke(cli_mod.cli, ["check", "--format", "json", "."])
        data = json.loads(r.output)  # stdout must be only JSON
        assert r.exit_code == 1
        assert data["is_compliant"] is False
        assert data["total_violations"] == len(data["violations"]) >= 1

    with runner.isolated_filesystem():
        Path("ok.py").write_text("x = 1\n")
        r = runner.invoke(cli_mod.cli, ["check", "--format", "json", "."])
        assert r.exit_code == 0 and json.loads(r.output)["is_compliant"] is True


def test_format_markdown_emits_report(monkeypatch):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("ok.py").write_text("x = 1\n")
        r = runner.invoke(cli_mod.cli, ["check", "--format", "markdown", "."])
        assert r.exit_code == 0
        assert r.output.startswith("# Anchor Governance Audit Report")


def test_format_json_still_honours_require_verified_governance(monkeypatch):
    monkeypatch.setattr(cli_mod, "_governance_status", lambda: (False, "modified: x"))
    monkeypatch.setenv("ANCHOR_REQUIRE_VERIFIED_GOVERNANCE", "1")
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("ok.py").write_text("x = 1\n")
        assert runner.invoke(cli_mod.cli, ["check", "--format", "json", "."]).exit_code == 2


def test_init_never_prompts_without_a_tty():
    """CliRunner stdin is not a TTY: init must finish instead of waiting for input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        r = runner.invoke(cli_mod.cli, ["init"], input="")
        assert r.exit_code == 0, r.output
        assert "Aborted" not in r.output
        assert Path(".anchor/keys/ed25519_private.pem").exists()


# ---------------------------------------------------------------- option order, version
def test_options_are_accepted_after_the_path(monkeypatch):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.py").write_text(BAD)
        r = runner.invoke(cli_mod.cli, ["check", ".", "--format", "json"])
        assert "Path not found" not in r.output
        assert json.loads(r.output)["total_violations"] >= 1


def test_version_flag_reports_package_version():
    r = CliRunner().invoke(cli_mod.cli, ["--version"])
    assert r.exit_code == 0
    assert r.output.startswith("anchor, version ")
    assert r.output.strip().split()[-1] == cli_mod._pkg_version()


# ---------------------------------------------------------------- --severity
def _json_scan(args, monkeypatch, source=BAD):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.py").write_text(source)
        r = runner.invoke(cli_mod.cli, ["check", *args, "."])
        return r, json.loads(r.output)


def test_default_severity_keeps_all_findings_and_reports_declared_severity(monkeypatch):
    r, data = _json_scan(["--format", "json"], monkeypatch)
    assert data["total_violations"] == 2  # eval + os.system
    assert {v["severity"] for v in data["violations"]} == {"blocker"}  # as declared by SEC-010 / SEC-007


def test_severity_threshold_never_hides_findings_that_meet_it(monkeypatch):
    r, data = _json_scan(["--format", "json", "--severity", "blocker"], monkeypatch)
    assert r.exit_code == 1 and data["total_violations"] == 2


def test_severity_threshold_filters_lower_findings_and_exit_code(monkeypatch):
    # Pretend the rules only declare "warning": a default (error) gate must ignore them.
    monkeypatch.setattr(cli_mod, "_declared_rule_severities", lambda: {"SEC-010": "warning", "SEC-007": "warning"})
    r, data = _json_scan(["--format", "json"], monkeypatch)
    assert r.exit_code == 0 and data["total_violations"] == 0 and data["is_compliant"] is True
    r, data = _json_scan(["--format", "json", "--severity", "warning"], monkeypatch)
    assert r.exit_code == 1 and data["total_violations"] == 2


def test_effective_severity_prefers_declared_and_falls_back_to_scanner():
    effective = cli_mod._effective_severity
    assert effective({"aggregated_rule_ids": "SEC-010", "severity": "error"}) == "blocker"
    assert effective({"aggregated_rule_ids": "NOT-A-RULE", "severity": "warning"}) == "warning"
    assert effective({"aggregated_rule_ids": "", "severity": "bogus"}) == "error"


# ---------------------------------------------------------------- report text
def test_trace_uri_is_a_valid_file_uri(monkeypatch):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.py").write_text(BAD)
        out = runner.invoke(cli_mod.cli, ["check", "."]).output
        uris = [l.split("Trace URI:")[1].strip() for l in out.splitlines() if "Trace URI:" in l]
        assert uris and all(u.startswith("file:///") and not u.startswith("file:////") for u in uris)
        assert all("#L" in u for u in uris)


def test_sec007_and_sec010_have_specific_descriptions(monkeypatch):
    _verified(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.py").write_text(BAD)
        out = runner.invoke(cli_mod.cli, ["check", "."]).output
        assert "Manual code review required" not in out
        assert "os.system()" in out and "eval()" in out


# ---------------------------------------------------------------- telemetry
def test_telemetry_is_dispatched_in_machine_readable_mode_without_polluting_stdout(monkeypatch):
    _verified(monkeypatch)
    calls = []
    monkeypatch.setattr(cli_mod, "_dispatch_telemetry", lambda *a, **k: calls.append(a) or {"status": "LOGGED", "transaction_id": "x"})
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.py").write_text(BAD)
        r = runner.invoke(cli_mod.cli, ["check", "--format", "json", "."])
        json.loads(r.output)  # still pure JSON
        assert len(calls) == 1


def test_telemetry_helper_is_a_noop_unless_opted_in(monkeypatch):
    monkeypatch.delenv("ANCHOR_TELEMETRY", raising=False)
    assert cli_mod._dispatch_telemetry(".", True, {"risk_score": 0.0}, []) is None
