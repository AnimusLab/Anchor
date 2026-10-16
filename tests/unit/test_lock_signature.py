import base64
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import anchor.core.governance_signature as gs


def _sign(tmp_path, data: bytes):
    key = Ed25519PrivateKey.generate()
    lock = tmp_path / "GOVERNANCE.lock"
    lock.write_bytes(data)
    sig = key.sign(gs.normalize_lock_bytes(data))
    (tmp_path / "GOVERNANCE.lock.sig").write_text(
        json.dumps({"signature": base64.b64encode(sig).decode()})
    )
    raw = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return lock, raw.hex()


@pytest.mark.parametrize("variant", [b"a: 1\nb: 2\n", b"a: 1\r\nb: 2\r\n"])
def test_signature_survives_line_ending_changes(tmp_path, monkeypatch, variant):
    lock, hex_ = _sign(tmp_path, b"a: 1\nb: 2\n")
    monkeypatch.setattr(gs, "GOVERNANCE_PUBLIC_KEY_HEX", hex_)
    lock.write_bytes(variant)
    gs.verify_lock_signature(lock)


def test_tampering_still_detected(tmp_path, monkeypatch):
    lock, hex_ = _sign(tmp_path, b"a: 1\n")
    monkeypatch.setattr(gs, "GOVERNANCE_PUBLIC_KEY_HEX", hex_)
    lock.write_bytes(b"a: 2\n")
    with pytest.raises(gs.GovernanceSignatureError):
        gs.verify_lock_signature(lock)


def test_committed_lock_verifies_with_embedded_key():
    gs.verify_lock_signature(
        Path(gs.__file__).resolve().parents[1] / "governance" / "GOVERNANCE.lock"
    )
