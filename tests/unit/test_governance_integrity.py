"""Rule-file integrity: signed lock must match the shipped rules; CLI must report the truth."""
import base64
import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import anchor.core.governance_signature as gs


# ------------------------------------------------------------------ helpers
def make_signed_tree(tmp_path, monkeypatch):
    root = tmp_path / "governance"
    (root / "domains").mkdir(parents=True)
    (root / "constitution.anchor").write_text("type: manifest\n", newline="\n")
    (root / "domains" / "security.anchor").write_text("rules: []\n", newline="\n")
    key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(
        gs, "GOVERNANCE_PUBLIC_KEY_HEX",
        key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex(),
    )
    sign_tree(root, key)
    return root, key


def sign_tree(root, key):
    lock = root / "GOVERNANCE.lock"
    lock.write_text(gs.build_lock_text(root, "9.9.9"), newline="\n")
    sig = key.sign(gs.normalize_lock_bytes(lock.read_bytes()))
    (root / "GOVERNANCE.lock.sig").write_text(json.dumps({"signature": base64.b64encode(sig).decode()}))


# ------------------------------------------------------------------ tree verification
def test_valid_tree_verifies(tmp_path, monkeypatch):
    root, _ = make_signed_tree(tmp_path, monkeypatch)
    gs.verify_governance_tree(root)


def test_crlf_checkout_still_verifies(tmp_path, monkeypatch):
    root, _ = make_signed_tree(tmp_path, monkeypatch)
    for f in root.rglob("*.anchor"):
        f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
    gs.verify_governance_tree(root)


def test_modified_rule_is_detected(tmp_path, monkeypatch):
    root, _ = make_signed_tree(tmp_path, monkeypatch)
    (root / "domains" / "security.anchor").write_text("rules: [evil]\n")
    with pytest.raises(gs.GovernanceSignatureError, match="modified: domains/security.anchor"):
        gs.verify_governance_tree(root)


def test_unlisted_rule_file_is_detected(tmp_path, monkeypatch):
    root, _ = make_signed_tree(tmp_path, monkeypatch)
    (root / "domains" / "extra.anchor").write_text("rules: []\n")
    with pytest.raises(gs.GovernanceSignatureError, match="unlisted: domains/extra.anchor"):
        gs.verify_governance_tree(root)


def test_missing_rule_file_is_detected(tmp_path, monkeypatch):
    root, _ = make_signed_tree(tmp_path, monkeypatch)
    (root / "domains" / "security.anchor").unlink()
    with pytest.raises(gs.GovernanceSignatureError, match="missing: domains/security.anchor"):
        gs.verify_governance_tree(root)


def test_edited_lock_breaks_signature(tmp_path, monkeypatch):
    root, _ = make_signed_tree(tmp_path, monkeypatch)
    lock = root / "GOVERNANCE.lock"
    lock.write_text(lock.read_text().replace("9.9.9", "1.0.0"))
    with pytest.raises(gs.GovernanceSignatureError):
        gs.verify_governance_tree(root)


def test_legacy_flat_lock_layout_is_understood():
    data = {"client_version": "6.0.1", "domains/a.anchor": "ab" * 32}
    assert gs.lock_files_from_data(data) == {"domains/a.anchor": "ab" * 32}
    assert gs.lock_files_from_data({"files": {"x.anchor": "cd" * 32}}) == {"x.anchor": "cd" * 32}


def test_committed_lock_matches_shipped_rules():
    """Fails if a *.anchor file changed without `python scripts/update_governance_lock.py`."""
    gs.verify_governance_tree(Path(gs.__file__).resolve().parents[1] / "governance")


# ------------------------------------------------------------------ CLI honesty
def _cli():
    from anchor.cli import cli
    return cli


def test_drift_command_does_not_claim_success():
    r = CliRunner().invoke(_cli(), ["drift"])
    assert r.exit_code == 2 and "not implemented" in r.output and "History verified" not in r.output


def test_verify_sync_detects_and_fixes_mismatch():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("sub").mkdir()
        Path("sub/mitigation.anchor").write_text("tampered\n")
        bad = runner.invoke(_cli(), ["verify-sync"])
        assert bad.exit_code == 1 and "MISMATCH" in bad.output
        fixed = runner.invoke(_cli(), ["verify-sync", "--fix"])
        assert fixed.exit_code == 0
        assert runner.invoke(_cli(), ["verify-sync"]).exit_code == 0


def test_sync_restore_requires_anchor_dir_and_verified_source(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        assert runner.invoke(_cli(), ["sync", "--restore"]).exit_code == 1  # no .anchor/
        Path(".anchor").mkdir()
        monkeypatch.setattr(gs, "verify_governance_tree", lambda *_a, **_k: (_ for _ in ()).throw(gs.GovernanceSignatureError("bad")))
        refused = runner.invoke(_cli(), ["sync", "--restore"])
        assert refused.exit_code == 1 and "Refusing to restore" in refused.output
        monkeypatch.setattr(gs, "verify_governance_tree", lambda *_a, **_k: None)
        ok = runner.invoke(_cli(), ["sync", "--restore"])
        assert ok.exit_code == 0 and Path(".anchor/domains/security.anchor").exists()


@pytest.mark.parametrize("verified,expect", [(True, "match the signed GOVERNANCE.lock"), (False, "UNVERIFIED RULE SET")])
def test_check_footer_reflects_real_verification(monkeypatch, verified, expect):
    import anchor.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_governance_status", lambda: (verified, "" if verified else "modified: x.anchor"))
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("ok.py").write_text("x = 1\n")
        r = runner.invoke(cli_mod.cli, ["check", "."])
        assert expect in r.output and "not legal advice" in r.output


def test_check_can_require_verified_governance(monkeypatch):
    import anchor.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_governance_status", lambda: (False, "modified: x.anchor"))
    monkeypatch.setenv("ANCHOR_REQUIRE_VERIFIED_GOVERNANCE", "1")
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("ok.py").write_text("x = 1\n")
        assert runner.invoke(cli_mod.cli, ["check", "."]).exit_code == 2


def test_check_fails_on_missing_path_instead_of_reporting_clean():
    runner = CliRunner()
    with runner.isolated_filesystem():
        r = runner.invoke(_cli(), ["check", "does-not-exist"])
        assert r.exit_code == 2 and "Path not found" in r.output
        hint = runner.invoke(_cli(), ["check", "drift"])
        assert hint.exit_code == 2 and "Did you mean `anchor drift`" in hint.output
