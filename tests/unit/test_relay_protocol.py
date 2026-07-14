import os
import json
import time
import pytest
from pathlib import Path

from anchor.runtime.relay_protocol import (
    encrypt_payload,
    decrypt_payload,
    SpokeRelayClient,
    MockHubServer
)

def test_encryption_decryption():
    """Verify built-in SHA256-CTR stream cipher."""
    secret_key = "my_super_secret_signing_key_123"
    plaintext = "Sensitive AI Prompt: what is the secret recipe?"
    
    iv, ciphertext = encrypt_payload(plaintext, secret_key)
    assert iv is not None
    assert ciphertext is not None
    assert ciphertext != plaintext
    
    decrypted = decrypt_payload(iv, ciphertext, secret_key)
    assert decrypted == plaintext


def test_relay_protocol_flow(tmp_path):
    """Verify end-to-end metadata relay and forensic pull flow."""
    secret_key = "signing_key_abc"
    port = 9876
    
    # 1. Setup a dummy local audit log
    log_path = tmp_path / "chain.jsonl"
    mock_entry = {
        "entry_id": "decision_9999",
        "timestamp": "2026-06-09T12:00:00Z",
        "governance_status": {
            "is_compliant": False,
            "status": "VIOLATION"
        },
        "cryptography": {
            "chain_hash": "chain_hash_xyz",
            "signature": "sig_xyz"
        },
        "violations": [{"rule_id": "SEC-007", "message": "Shell injection"}],
        "telemetry": {
            "prompt_preview": "user prompt text",
            "response_preview": "blocked"
        }
    }
    log_path.write_text(json.dumps(mock_entry) + "\n", encoding="utf-8")

    # 2. Start Mock Hub Server
    hub = MockHubServer(host="127.0.0.1", port=port)
    hub.start()
    
    # 3. Start Spoke Client (pointing to Hub and the dummy log)
    spoke = SpokeRelayClient(
        host="127.0.0.1",
        port=port,
        secret_key=secret_key,
        audit_log_path=str(log_path)
    )
    spoke.start()
    
    try:
        # Wait for connection to establish (up to 5 seconds)
        for _ in range(50):
            if spoke.ws and hub.active_ws:
                break
            time.sleep(0.1)
        
        # 4. Dispatch lightweight ZK header from Spoke to Hub
        spoke.send_header(mock_entry)
        
        # Wait for header to be received (up to 5 seconds)
        for _ in range(50):
            if len(hub.received_headers) == 1:
                break
            time.sleep(0.1)
        
        # Verify ZK header received at Hub
        assert len(hub.received_headers) == 1
        received_hdr = hub.received_headers[0]
        assert received_hdr["entry_id"] == "decision_9999"
        assert received_hdr["chain_hash"] == "chain_hash_xyz"
        assert received_hdr["status"] == "VIOLATION"
        
        # 5. Issue FORENSIC_PULL from Hub to Spoke
        pull_response = hub.request_forensic_pull("decision_9999", timeout=2.0)
        assert pull_response is not None
        assert "error" not in pull_response
        
        # 6. Decrypt the payload received at the Hub
        iv = pull_response["iv"]
        ciphertext = pull_response["payload"]
        decrypted_raw = decrypt_payload(iv, ciphertext, secret_key)
        
        decrypted_payload = json.loads(decrypted_raw)
        
        # Verify decrypted payload matches original sensitive data
        assert decrypted_payload["telemetry"]["prompt_preview"] == "user prompt text"
        assert decrypted_payload["violations"][0]["rule_id"] == "SEC-007"
        
    finally:
        spoke.stop()
        hub.stop()
