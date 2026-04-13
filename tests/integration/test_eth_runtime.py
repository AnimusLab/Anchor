import pytest
import os
import json
from anchor.runtime.decision_auditor import DecisionAuditor

# Ensure we are in a clean state and have the ethics rules loaded
@pytest.fixture(autouse=True)
def setup_auditor():
    # Force warm-up if not already done
    auditor = DecisionAuditor()
    return auditor

def test_eth_001_redlining_detection():
    """Verifies that geographic proxies (Redlining) are detected in structured mode."""
    auditor = DecisionAuditor()
    response = {
        "ReasonCode": "ID_003",
        "FeatureAttribution": "Application denied due to neighborhood risk profile"
    }
    violations = auditor.check_eth_compliance(response, mode="structured")
    
    eth_001 = [v for v in violations if v["rule_id"] == "ETH-001"]
    assert len(eth_001) > 0
    assert any(v["concept"] == "Redlining" for v in eth_001)
    assert any("neighborhood" in v["detected_term"] for v in eth_001)

def test_eth_002_prose_blocked():
    """Verifies that plain text is blocked when the engine expects structured JSON."""
    auditor = DecisionAuditor()
    response = "Your application has been denied."
    violations = auditor.check_eth_compliance(response, mode="structured")
    
    assert any(v["rule_id"] == "ETH-002" for v in violations)
    assert "Prose returned in structured mode" in violations[0]["description"]

def test_eth_001_clean_decision():
    """Verifies that non-discriminatory, structured decisions pass without violations."""
    auditor = DecisionAuditor()
    response = {
        "ReasonCode": "ID_001",
        "FeatureAttribution": "Debt-to-income ratio exceeded threshold"
    }
    violations = auditor.check_eth_compliance(response, mode="structured")
    assert len(violations) == 0

def test_eth_001_conversational_pii():
    """Verifies multi-proxy detection in raw conversational text."""
    auditor = DecisionAuditor()
    response = "Based on your zip code and marital status, we cannot proceed."
    violations = auditor.check_eth_compliance(response, mode="conversational")
    
    eth_001_violations = [v for v in violations if v["rule_id"] == "ETH-001"]
    concepts = [v["concept"] for v in eth_001_violations]
    
    assert "Redlining" in concepts
    assert "Gender Bias" in concepts
    assert len(eth_001_violations) >= 2
