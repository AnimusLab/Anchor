import pytest
from anchor.cli import AnchorEngine


def test_rust_engine_instantiation():
    engine = AnchorEngine()
    assert engine.version() == "6.0.0"


def test_ed25519_keypair_generation_and_signing():
    engine = AnchorEngine()
    kp = engine.generate_keypair()
    assert "private_key_pem" in kp
    assert "public_key_pem" in kp
    assert "fingerprint" in kp

    chain_hash = "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    priv_key_hex = "00" * 32
    pub_key_hex = "00" * 32

    sig = engine.sign_ed25519(chain_hash, priv_key_hex)
    assert sig is not None

def test_zero_copy_audit_payload():
    engine = AnchorEngine()
    payload = b'api_key = "your-replicate-api-key"'
    res = engine.audit_payload(payload)
    assert res["is_compliant"] is False
    assert "SEC-002" in res["matched_rule_ids"]
