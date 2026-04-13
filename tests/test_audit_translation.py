import json
import pytest
from anchor.runtime.models import AuditEntry

def test_audit_translation():
    # 1. Create a mock AuditEntry with a specific violation (ETH-001)
    entry = AuditEntry(
        entry_id="test_id_123",
        timestamp="2026-04-02T13:05:00Z",
        jurisdiction="INDIA",
        provider="openai",
        project_name="anchor-runtime",
        git_commit="deadbeef123",
        is_compliant=False,
        status="VIOLATION",
        findings_hash="findings_hash_456",
        prev_chain_hash="prev_hash_789",
        chain_hash="chain_hash_000",
        signature="signature_abc",
        violations=[{
            "rule_id": "ETH-001",
            "description": "ECOA Section 701(a) - Prohibited Proxy Detection",
            "file_path": "finance/models.py"
        }],
        telemetry={
            "latency_ms": 150.0,
            "detected_proxy": "zip_code",
            "prompt_preview": "Analyze this loan application for zip code 90210..."
        }
    )

    # 2. Verify RBI Translation
    rbi = entry.to_rbi_json(entity_name="Goldman_Sachs_India")
    print("\n[VERIFY] RBI Output:")
    print(json.dumps(rbi, indent=2))
    assert rbi["regulatory_body"] == "RBI"
    assert "Sutra 4" in rbi["sutra_alignment"] # Fairness
    assert rbi["incident_metadata"]["entity_id"] == "Goldman_Sachs_India"

    # 3. Verify SEC Translation
    sec = entry.to_sec_json()
    print("\n[VERIFY] SEC Output:")
    print(json.dumps(sec, indent=2))
    assert sec["form_type"] == "8-K / Item 1.05"
    assert sec["materiality_signal"] == "HIGH"
    assert "Effectively Mitigated" in sec["governance_event"]["control_status"]

    # 4. Verify EU AI Act Translation
    eu = entry.to_eu_article12_json()
    print("\n[VERIFY] EU AI Act Output:")
    print(json.dumps(eu, indent=2))
    assert eu["article"] == "12.2 (Logging)"
    assert "ISO/IEC 42001:2023" in eu["conformity_declaration"]
    assert eu["integrity_proof"] == "signature_abc"

if __name__ == "__main__":
    try:
        test_audit_translation()
        print("\n[SUCCESS] Audit Translation Layer Verification Complete\n")
    except Exception as e:
        print(f"\n[ERROR] Audit Translation Layer Verification Failed: {e}\n")
        exit(1)
