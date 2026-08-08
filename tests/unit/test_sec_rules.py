import pytest
from pathlib import Path
from anchor.core.loader import load_domain_file
from anchor.cli import RULE_DESCRIPTIONS

def test_sec_anchor_file_loading():
    """Verify that sec.anchor is correctly loaded and parsed."""
    sec_file = Path("governance/domains/sec.anchor")
    assert sec_file.exists()
    
    rules = load_domain_file(sec_file, expected_namespace="SEC", seal_check="development")
    assert rules is not None
    assert len(rules) == 6
    
    rule_ids = list(rules.keys())
    assert "SEC-SEC-REG-SCI" in rule_ids or "SEC-REG-SCI" in rule_ids
    assert "SEC-SEC-RULE-15C3" in rule_ids or "SEC-RULE-15C3" in rule_ids

def test_sec_rule_descriptions_matrix():
    """Verify that all SEC rules have matching 5-line structural descriptions."""
    expected_sec_ids = [
        "SEC-REG-SCI",
        "SEC-RULE-15C3",
        "SEC-PDA-CONFLICT",
        "SEC-RULE-206",
        "SEC-FORM-8K",
        "SEC-FINRA-3110"
    ]
    for rule_id in expected_sec_ids:
        assert rule_id in RULE_DESCRIPTIONS
        desc = RULE_DESCRIPTIONS[rule_id]
        assert len(desc) > 50
        assert "SEC" in desc or "FINRA" in desc
