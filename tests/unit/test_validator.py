import pytest
from pathlib import Path
from anchor.core.validator import AnchorFileValidator

def test_determine_type():
    assert AnchorFileValidator.determine_type({"type": "manifest"}, Path("dummy.anchor")) == "manifest"
    assert AnchorFileValidator.determine_type({"type": "domain"}, Path("dummy.anchor")) == "domain"
    assert AnchorFileValidator.determine_type({}, Path("constitution.anchor")) == "manifest"
    assert AnchorFileValidator.determine_type({}, Path("policy.anchor")) == "policy"
    assert AnchorFileValidator.determine_type({}, Path("domains/security.anchor")) == "domain"
    assert AnchorFileValidator.determine_type({}, Path("frameworks/NIST.anchor")) == "framework"
    assert AnchorFileValidator.determine_type({}, Path("government/EU.anchor")) == "framework"
    assert AnchorFileValidator.determine_type({}, Path("unknown.anchor")) == "unknown"

def test_validate_manifest():
    # Valid manifest
    valid_manifest = {
        "version": "1.0",
        "anchor_version": ">=1.0",
        "core_domains": [{"namespace": "SEC", "path": "domains/security.anchor"}],
        "engine": {},
        "policy": {},
        "legacy_aliases": {}
    }
    AnchorFileValidator.validate(Path("constitution.anchor"), valid_manifest)

    # Missing required field
    invalid_manifest = {
        "version": "1.0"
    }
    with pytest.raises(ValueError, match="missing required fields"):
        AnchorFileValidator.validate(Path("constitution.anchor"), invalid_manifest)

    # Duplicate namespace
    duplicate_ns = {
        "version": "1.0",
        "anchor_version": ">=1.0",
        "core_domains": [
            {"namespace": "SEC", "path": "domains/security.anchor"},
            {"namespace": "SEC", "path": "domains/sec2.anchor"}
        ]
    }
    with pytest.raises(ValueError, match="Duplicate namespace 'SEC'"):
        AnchorFileValidator.validate(Path("constitution.anchor"), duplicate_ns)

def test_validate_domain():
    # Valid domain
    valid_domain = {
        "type": "domain",
        "namespace": "ETH",
        "rules": [{"id": "ETH-001", "name": "Rule"}]
    }
    AnchorFileValidator.validate(Path("ethics.anchor"), valid_domain)

    # Missing namespace
    invalid_domain = {
        "type": "domain",
        "rules": []
    }
    with pytest.raises(ValueError, match="missing required field: 'namespace'"):
        AnchorFileValidator.validate(Path("ethics.anchor"), invalid_domain)

def test_validate_framework():
    # Valid framework
    valid_fw = {
        "type": "framework",
        "namespace": "NIST",
        "rules": [{"id": "NIST-1", "name": "Mapping"}]
    }
    AnchorFileValidator.validate(Path("nist.anchor"), valid_fw)

def test_validate_policy():
    # Valid policy
    valid_policy = {
        "type": "policy",
        "rules": [{"id": "SEC-001", "severity": "error"}]
    }
    AnchorFileValidator.validate(Path("policy.anchor"), valid_policy)
