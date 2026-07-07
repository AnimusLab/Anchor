import os
import json
import pytest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from anchor.governance.event import Actor, PolicyBinding, GovernanceEvent
from anchor.governance.keys import GovernanceKeyManager
from anchor.governance.policy import PolicyRegistry
from anchor.governance.emitter import GovernanceEmitter
from anchor.governance.reconstruction import DecisionReconstructor

def test_actor_and_binding_dataclasses():
    actor = Actor(id="user-123", principal="user@example.com", roles=["admin"])
    assert actor.id == "user-123"
    assert actor.principal == "user@example.com"
    assert actor.roles == ["admin"]
    assert actor.session_id is None
    assert actor.auth_source == "unknown"

    binding = PolicyBinding(policy_version="v5.3.1", policy_hash="abc123hash")
    assert binding.policy_version == "v5.3.1"
    assert binding.policy_hash == "abc123hash"
    assert binding.authority_url is None

def test_event_canonical_json_and_signing():
    actor = Actor(id="user-123", principal="user@example.com", roles=["admin"])
    binding = PolicyBinding(policy_version="v5.3.1", policy_hash="abc123hash")
    event = GovernanceEvent.create(
        event_type="TOOL_EXECUTED",
        actor=actor,
        policy_binding=binding,
        details={"tool": "test_tool"},
        checkpoint_id="chk-001"
    )

    canonical = event.canonical_json()
    parsed = json.loads(canonical)
    assert "signature" not in parsed
    assert parsed["checkpoint_id"] == "chk-001"
    assert parsed["actor"]["id"] == "user-123"

    # Generate Ed25519 key pair
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Sign event
    event.sign(private_key)
    assert event.signature is not None

    # Verify signature
    assert event.verify(public_key) is True

    # Tamper event details and check that verification fails
    original_tool = event.details["tool"]
    event.details["tool"] = "tampered_tool"
    assert event.verify(public_key) is False
    event.details["tool"] = original_tool

def test_key_manager(tmp_path):
    keystore_file = tmp_path / "test_governance.keystore"
    km = GovernanceKeyManager(keystore_path=str(keystore_file))

    # Test before generating/unlocking
    assert km.private_key is None
    assert km.get_public_key_hex() == ""

    # Generate keystore
    km.generate_keystore()
    assert km.private_key is not None
    pub_hex = km.get_public_key_hex()
    assert len(pub_hex) > 0

    # Create new manager and unlock
    km2 = GovernanceKeyManager(keystore_path=str(keystore_file))
    success = km2.unlock("test-password")  # Password currently ignored/simulated
    assert success is True
    assert km2.get_public_key_hex() == pub_hex

def test_policy_registry(tmp_path):
    constitution_file = tmp_path / "constitution.anchor"
    registry = PolicyRegistry(constitution_path=str(constitution_file))

    # Test fallback
    binding_fallback = registry.get_current_binding()
    assert binding_fallback.policy_hash is not None
    assert len(binding_fallback.policy_hash) == 64

    # Write content
    content = "domain: security\nactive: true"
    constitution_file.write_text(content, encoding="utf-8")

    binding = registry.get_current_binding()
    import hashlib
    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert binding.policy_hash == expected_hash
    assert registry.verify_hash(expected_hash) is True
    assert registry.verify_hash("wrong_hash") is False

def test_emitter_and_reconstructor(tmp_path):
    log_file = tmp_path / "governance_events.jsonl"
    keystore_file = tmp_path / "governance.keystore"
    constitution_file = tmp_path / "constitution.anchor"

    # Set up files
    constitution_file.write_text("domain: security", encoding="utf-8")
    
    # Emitter setup
    emitter = GovernanceEmitter(log_path=str(log_file))
    emitter.policy_registry = PolicyRegistry(constitution_path=str(constitution_file))
    emitter.key_manager = GovernanceKeyManager(keystore_path=str(keystore_file))
    emitter.key_manager.generate_keystore()

    actor = Actor(id="operator", principal="ops@anchor", roles=["operator"])
    
    # Emit event
    event = emitter.emit(
        event_type="TOOL_EXECUTED",
        actor=actor,
        details={"tool": "run_command"},
        checkpoint_id="chk-abc"
    )
    assert event.signature is not None

    # Verify log file has event
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    log_entry = json.loads(lines[0])
    assert log_entry["event"]["checkpoint_id"] == "chk-abc"

    # Reconstructor setup
    reconstructor = DecisionReconstructor(log_path=str(log_file))
    history = reconstructor.get_decision_history("chk-abc")
    assert len(history) == 1
    assert history[0]["event_id"] == event.event_id

    # Verify decision
    policy_hash = emitter.policy_registry.get_current_binding().policy_hash
    pub_key = emitter.key_manager.private_key.public_key()
    
    verdict = reconstructor.verify_decision("chk-abc", policy_hash, pub_key)
    assert verdict["valid"] is True
    assert verdict["event_count"] == 1
    assert verdict["final_event_type"] == "TOOL_EXECUTED"

    # Verify decision fails with wrong policy hash
    verdict_bad_hash = reconstructor.verify_decision("chk-abc", "bad_hash", pub_key)
    assert verdict_bad_hash["valid"] is False
    assert verdict_bad_hash["reason"] == "Policy hash mismatch"

    # Verify decision fails with wrong signature/wrong public key
    bad_private = ed25519.Ed25519PrivateKey.generate()
    bad_pub = bad_private.public_key()
    verdict_bad_sig = reconstructor.verify_decision("chk-abc", policy_hash, bad_pub)
    assert verdict_bad_sig["valid"] is False
    assert "signature verification failed" in verdict_bad_sig["reason"].lower()

def test_get_code_snippet(tmp_path):
    from anchor.cli import _get_code_snippet

    # Test non-existent file
    assert _get_code_snippet(str(tmp_path / "non_existent.py"), 5) == ""

    # Create dummy file
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("line 1\n  line 2 with spacing  \nline 3\n", encoding="utf-8")

    # Test valid lines
    assert _get_code_snippet(str(dummy_file), 1) == "line 1"
    assert _get_code_snippet(str(dummy_file), 2) == "line 2 with spacing"
    assert _get_code_snippet(str(dummy_file), 3) == "line 3"

    # Test out of bounds
    assert _get_code_snippet(str(dummy_file), 0) == ""
    assert _get_code_snippet(str(dummy_file), 4) == ""


def test_local_keypair_generation_pem(tmp_path):
    private_pem_path = tmp_path / "ed25519_private.pem"
    public_pem_path = tmp_path / "ed25519_public.pem"
    
    km = GovernanceKeyManager(
        private_key_path=str(private_pem_path),
        public_key_path=str(public_pem_path)
    )
    
    # Assert keys do not exist initially
    assert not private_pem_path.exists()
    assert not public_pem_path.exists()
    
    # Generate keys
    km.generate_keypair_pem()
    assert private_pem_path.exists()
    assert public_pem_path.exists()
    assert km.private_key is not None
    
    # Verify public key is retrievable
    pub_hex = km.get_public_key_hex()
    assert len(pub_hex) > 0
    
    # Create a new manager and unlock using PEM file
    km2 = GovernanceKeyManager(
        private_key_path=str(private_pem_path),
        public_key_path=str(public_pem_path)
    )
    assert km2.private_key is None
    assert km2.unlock() is True
    assert km2.private_key is not None
    assert km2.get_public_key_hex() == pub_hex


