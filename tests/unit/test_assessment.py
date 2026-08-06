import pytest
from anchor.core.assessment import ArchitecturalAssessmentEngine, generate_executive_summary_text

def test_assess_security_compliance_empty():
    clusters = ArchitecturalAssessmentEngine.assess_security_compliance([])
    assert clusters == []
    assert generate_executive_summary_text(clusters) == ""

def test_assess_security_compliance_with_violations():
    violations = [
        {"id": "SEC-007", "file": "app.py", "line": 42, "line_content": "subprocess.run(['ls'])"},
        {"id": "SEC-002", "file": "db.py", "line": 10, "line_content": "api_key='sk-test'"},
        {"id": "ALN-001", "file": "llm.py", "line": 15, "line_content": "chat.completions.create()"},
    ]
    clusters = ArchitecturalAssessmentEngine.assess_security_compliance(violations)
    assert len(clusters) >= 3
    titles = [c.title for c in clusters]
    assert "Unsandboxed Agent Execution" in titles
    assert "Runtime Governance Missing" in titles
    assert "Security Compliance Gap (SEC)" in titles
    assert "Security Compliance Gap (ALN)" in titles

    summary_text = generate_executive_summary_text(clusters)
    assert "=== EXECUTIVE SUMMARY ===" in summary_text
    assert "ROOT GOVERNANCE RISK #1" in summary_text
    assert "Unsandboxed Agent Execution" in summary_text
