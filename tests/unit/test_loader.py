import pytest
import yaml
from anchor.core.policy_loader import PolicyLoader, _severity_rank

def test_severity_rank():
    assert _severity_rank("info") < _severity_rank("warning")
    assert _severity_rank("warning") < _severity_rank("error")
    assert _severity_rank("error") < _severity_rank("blocker")
    assert _severity_rank("blocker") < _severity_rank("critical")

def test_merge_policies_overrides():
    loader = PolicyLoader("local.anchor")
    parent = {
        "version": "1.0",
        "rules": [
            {"id": "SEC-001", "name": "Rule 1", "severity": "warning"}
        ]
    }
    local = {
        "rules": [
            {"id": "SEC-001", "severity": "error"}
        ]
    }
    
    merged = loader._merge_policies(parent, local)
    
    # Check that severity was upgraded
    rule = next(r for r in merged["rules"] if r["id"] == "SEC-001")
    assert rule["severity"] == "error"
    # Check that name was preserved from parent
    assert rule["name"] == "Rule 1"

def test_merge_policies_floor_severity():
    loader = PolicyLoader("local.anchor")
    parent = {
        "rules": [
            {"id": "SEC-001", "severity": "blocker", "min_severity": "error"}
        ]
    }
    # Local tries to downgrade below floor
    local = {
        "rules": [
            {"id": "SEC-001", "severity": "warning"}
        ]
    }
    
    merged = loader._merge_policies(parent, local)
    
    # Check that severity was forced back to floor
    rule = next(r for r in merged["rules"] if r["id"] == "SEC-001")
    assert rule["severity"] == "error"

def test_merge_policies_exclude_union():
    loader = PolicyLoader("local.anchor")
    parent = {"exclude": ["tests/*"]}
    local = {"exclude": ["vendor/**/*"]}
    
    merged = loader._merge_policies(parent, local)
    
    assert set(merged["exclude"]) == {"tests/*", "vendor/**/*"}
