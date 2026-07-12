import re
import hmac
import hashlib
import json
from unittest.mock import patch, MagicMock
from anchor.runtime.decision_auditor import DecisionAuditor
from anchor.runtime.models import AuditEntry

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
