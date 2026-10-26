import json

import pytest

pytest.importorskip("cryptography")
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from anchor.core.telemetry import SpokeTelemetryClient


@pytest.fixture
def init_keypair(tmp_path, monkeypatch):
    """Keys exactly as `anchor init` writes them."""
    from click.testing import CliRunner
    from anchor.cli import cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANCHOR_PRIVATE_KEY_PATH", raising=False)
    result = CliRunner().invoke(cli, ["init", "--no-prompt"])
    assert result.exit_code == 0, result.output
    fingerprint = [l for l in result.output.splitlines() if "Fingerprint" in l][0]
    fingerprint = "sha256:" + fingerprint.split("sha256:")[1].rstrip(")").strip()
    return tmp_path, fingerprint


def test_init_keys_load_and_fingerprint_matches_init(init_keypair):
    _, printed = init_keypair
    client = SpokeTelemetryClient(enabled=False)
    assert client.private_key is not None
    assert client.identity_fingerprint == printed


def test_signature_verifies_against_init_public_key(init_keypair):
    tmp, _ = init_keypair
    client = SpokeTelemetryClient(enabled=False)
    payload = b'{"event":"x"}'
    sig = bytes.fromhex(client.sign_payload(payload))
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex((tmp / ".anchor/keys/ed25519_public.pem").read_text().strip()))
    pub.verify(sig, payload)  # raises InvalidSignature on failure


def test_dispatch_includes_signature_header(init_keypair, monkeypatch):
    seen = {}

    class _Resp:
        status = 200

        def read(self):
            return b'{"transaction_id": "tx1"}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, *a, **k):
        seen["headers"] = {k.lower(): v for k, v in req.header_items()}
        seen["body"] = req.data
        return _Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    monkeypatch.setattr("anchor.core.telemetry.HAS_HTTPX", False)
    client = SpokeTelemetryClient(enabled=True, hub_url="http://127.0.0.1:9")
    client.dispatch_state_event(
        event_id="evt_1", project_name="p", silo_id="s", verdict="NON_COMPLIANT", risk_score=3.0, violations=[]
    )
    assert "x-anchor-signature" in seen.get("headers", {})
    assert json.loads(seen["body"])["identity_fingerprint"].startswith("sha256:")
    assert json.loads(seen["body"])["identity_fingerprint"] != "sha256:ed25519_node_sovereign_key"


def test_pem_and_raw_keys_still_load(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    monkeypatch.chdir(tmp_path)
    key = Ed25519PrivateKey.generate()
    pem = tmp_path / "k.pem"
    pem.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    assert SpokeTelemetryClient(enabled=False, private_key_path=str(pem)).private_key is not None
    raw = tmp_path / "k.raw"
    raw.write_bytes(key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
    assert SpokeTelemetryClient(enabled=False, private_key_path=str(raw)).private_key is not None


def test_garbage_key_falls_back_without_crashing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad = tmp_path / "bad.pem"
    bad.write_text("not a key at all")
    client = SpokeTelemetryClient(enabled=False, private_key_path=str(bad))
    assert client.private_key is None
