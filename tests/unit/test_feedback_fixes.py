import re
import hmac
import hashlib
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from anchor.runtime.decision_auditor import DecisionAuditor
from anchor.runtime.models import AuditEntry
from anchor.governance.reconstruction import DecisionReconstructor
from anchor.runtime.relay_protocol import SpokeRelayClient
from anchor.governance.emitter import GovernanceEmitter

def test_sec_004_regex_compilation():
    # Verify that the SEC-004 regex pattern compiles and executes without errors in Python
    # (Checking the fix for "global flags not at the start of the expression")
    pattern = r"(?i)^(?:[^\"\'#]|([\"'])(?:(?!\1).|\\\1)*\1)*\bos\.(environ\.(copy|items)\(\)|\benviron\b\s*\[.*(TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL|API).*\]|\{\*\*os\.environ)"
    
    # Try compiling
    compiled = re.compile(pattern)
    assert compiled is not None
    
    # Try matching
    match_str = "os.environ['API_KEY']"
    assert compiled.search(match_str) is not None

def test_findings_hash_salting():
    # Verify that findings_hash is computed using HMAC-SHA256 and salted with entry_id
    # (So same rules with different entry_ids produce different findings_hash)
    auditor = DecisionAuditor()
    
    # Mock runtime chain hash retrieval
    auditor.get_last_runtime_hash = MagicMock(return_value="0".zfill(64))
    
    # Run audit 1
    entry1 = auditor.audit(
        provider="test-provider",
        prompt="test prompt",
        response="test response",
        findings=[{"rule_id": "SEC-004"}]
    )
    
    # Run audit 2 with same rules/inputs
    entry2 = auditor.audit(
        provider="test-provider",
        prompt="test prompt",
        response="test response",
        findings=[{"rule_id": "SEC-004"}]
    )
    
    # Verify entry_ids are different
    assert entry1["entry_id"] != entry2["entry_id"]
    
    # Verify findings_hashes are different (due to entry_id salting)
    assert entry1["cryptography"]["findings_hash"] != entry2["cryptography"]["findings_hash"]

def test_static_detectors_mitigations():
    # Test MIT-004-B (Hardcoded API Key / Secret) regex matches
    mit_004_b_pattern = r"(?i)(?:[a-zA-Z0-9_]*key|[a-zA-Z0-9_]*secret|[a-zA-Z0-9_]*token|password|credential)\s*=\s*['\"][a-zA-Z0-9_\-\.\:\/]{16,}['\"]"
    rx_004 = re.compile(mit_004_b_pattern)
    assert rx_004.search("openai_key = 'sk-proj-1234567890abcdef1234567890'") is not None
    assert rx_004.search("secret_key = \"mysecretkey12345\"") is not None
    assert rx_004.search("api-key = '12345'") is None # Too short (<16 chars)

    # Test MIT-010-A (Insecure Python Execution sinks) regex matches
    mit_010_a_pattern = r"(?i)\b(?:eval|exec|pickle\.loads|pickle\.load|marshal\.loads|shelve\.open)\s*\("
    rx_010 = re.compile(mit_010_a_pattern)
    assert rx_010.search("eval(user_code)") is not None
    assert rx_010.search("pickle.loads(payload)") is not None
    assert rx_010.search("other_func()") is None

def test_is_sealed_field():
    auditor = DecisionAuditor()
    auditor.get_last_runtime_hash = MagicMock(return_value="0".zfill(64))
    
    # 1. No secret configured -> is_sealed should be False
    with patch.dict('os.environ', {}, clear=True):
        entry_unsealed = auditor.audit(
            provider="test-provider",
            prompt="test prompt",
            response="test response",
            findings=[]
        )
        assert entry_unsealed["cryptography"]["is_sealed"] is False

    # 2. Secret configured -> is_sealed should be True
    with patch.dict('os.environ', {"ANCHOR_SECRET_KEY": "some-secret"}):
        entry_sealed = auditor.audit(
            provider="test-provider",
            prompt="test prompt",
            response="test response",
            findings=[]
        )
        assert entry_sealed["cryptography"]["is_sealed"] is True

def test_structured_mode_json_check():
    # Verify that valid JSON response strings or dicts do NOT fail the No-Prose rule ETH-002
    auditor = DecisionAuditor()
    
    # Non-JSON prose string in structured mode -> violation
    res1 = auditor.check_eth_compliance("This is plain text prose", mode="structured")
    assert any(v["rule_id"] == "ETH-002" for v in res1)

    # Valid JSON string with missing required fields -> violation
    res2 = auditor.check_eth_compliance('{"ReasonCode": "C1"}', mode="structured")
    assert any(v["rule_id"] == "ETH-002" and "Missing required fields" in v["description"] for v in res2)

    # Valid JSON string with all required fields -> COMPLIANT
    res3 = auditor.check_eth_compliance('{"ReasonCode": "C1", "FeatureAttribution": "A1"}', mode="structured")
    assert not any(v["rule_id"] == "ETH-002" for v in res3)

    # Dictionary with all required fields -> COMPLIANT
    res4 = auditor.check_eth_compliance({"ReasonCode": "C1", "FeatureAttribution": "A1"}, mode="structured")
    assert not any(v["rule_id"] == "ETH-002" for v in res4)

def test_unsealed_warning_to_stderr():
    # Verify that when ANCHOR_SECRET_KEY is missing, a warning is printed to stderr
    auditor = DecisionAuditor()
    auditor.get_last_runtime_hash = MagicMock(return_value="0".zfill(64))

    # Test unsealed warning
    with patch.dict('os.environ', {}, clear=True):
        with patch.object(sys.stderr, 'write') as mock_stderr:
            auditor.audit(
                provider="test-provider",
                prompt="test prompt",
                response="test response",
                findings=[]
            )
            mock_stderr.assert_called()
            # Ensure the word UNSEALED is printed to stderr
            calls = [c[0][0] for c in mock_stderr.call_args_list]
            stderr_output = "".join(calls)
            assert "WARNING: Audit chain is UNSEALED" in stderr_output

def test_reconstruction_connection(tmp_path):
    # Verify that DecisionAuditor.audit records a reconstructible GovernanceEvent
    log_file = tmp_path / "governance_events.jsonl"
    
    auditor = DecisionAuditor()
    auditor.get_last_runtime_hash = MagicMock(return_value="0".zfill(64))
    
    # Surgical mock of GovernanceEmitter.__init__ default path
    original_init = GovernanceEmitter.__init__
    def mock_init(self, *args, **kwargs):
        kwargs['log_path'] = str(log_file)
        original_init(self, *args, **kwargs)
        
    with patch.object(GovernanceEmitter, '__init__', mock_init):
        entry = auditor.audit(
            provider="test-provider",
            prompt="test prompt",
            response="test response",
            findings=[],
            checkpoint_id="test-chk-123"
        )
        
        # Verify event log file was created
        assert log_file.exists()
        
        # Verify the event can be reconstructed via DecisionReconstructor
        reconstructor = DecisionReconstructor(log_path=str(log_file))
        history = reconstructor.get_decision_history("test-chk-123")
        assert len(history) == 1
        assert history[0]["event_type"] == "decision_audit"
        assert history[0]["details"]["entry_id"] == entry["entry_id"]

def test_relay_recovery_on_reject():
    # Verify SpokeRelayClient raises RuntimeError on HUB_REJECT so connection retry is triggered
    client = SpokeRelayClient(host="localhost", port=8001, secret_key="test-key")
    client.running = True
    
    # Mock the websocket
    mock_ws = MagicMock()
    async def mock_recv():
        return json.dumps({"type": "HUB_REJECT", "payload": "deprovisioned"})
    mock_ws.recv = mock_recv
    mock_ws.send = MagicMock()
    
    # Mock the async context manager returned by websockets.connect
    mock_ctx = MagicMock()
    async def mock_aenter():
        return mock_ws
    async def mock_aexit(exc_type, exc_val, exc_tb):
        pass
    mock_ctx.__aenter__ = mock_aenter
    mock_ctx.__aexit__ = mock_aexit
    
    import pytest
    with patch('websockets.connect', return_value=mock_ctx):
        # We mock asyncio.sleep to raise a custom exception when the retry loop sleeps
        async def mock_sleep(seconds):
            raise RuntimeError("sleep_called")
            
        with patch('asyncio.sleep', mock_sleep):
            # Triggering _connect_and_listen with HUB_REJECT should raise RuntimeError from sleep mock
            import asyncio
            with pytest.raises(RuntimeError) as exc_info:
                asyncio.run(client._connect_and_listen())
            assert "sleep_called" in str(exc_info.value)
