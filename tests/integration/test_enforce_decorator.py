import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from dataclasses import dataclass

from anchor.runtime import enforce, activate, deactivate
from anchor.runtime.decision_auditor import DecisionAuditor

@dataclass
class MockResponse:
    content: str
    def __post_init__(self):
        self._anchor_audit = None

def test_enforce_decorator_conversational(tmp_path):
    """Verifies basic auditing for a conversational AI function."""
    # Reset singleton
    DecisionAuditor._is_warmed_up = False
    DecisionAuditor._shared_engine = None
    
    # Mock environment
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".anchor").mkdir()
    
    with patch("os.getcwd", return_value=str(project_dir)):
        # Define a mock AI function
        @enforce(jurisdiction="EU", custom_tag="test")
        def mock_ai_call(prompt: str):
            return MockResponse(content="Hello, this is a safe response.")

        # Call it
        result = mock_ai_call("Hello world")
        
        # Verify Audit Attachment
        assert hasattr(result, "_anchor_audit")
        audit = result._anchor_audit
        assert audit["governance_status"]["is_compliant"] is True
        assert audit["execution_context"]["jurisdiction"] == "EU"
        assert audit["execution_context"]["provider"] == "custom-decorator"

def test_enforce_decorator_structured_violation(tmp_path):
    """Verifies ETH-002 detection when prose is returned in structured mode."""
    DecisionAuditor._is_warmed_up = False
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".anchor").mkdir()

    with patch("os.getcwd", return_value=str(project_dir)):
        @enforce(mode="structured")
        def mock_structured_ai():
            return MockResponse(content="I am sorry, I cannot return JSON.")

        result = mock_structured_ai()
        
        audit = result._anchor_audit
        assert audit["governance_status"]["is_compliant"] is False
        
        rule_ids = [f["rule_id"] for f in audit["violations"]]
        assert "ETH-002" in rule_ids

def test_enforce_immutable_silent_fail(tmp_path):
    """Verifies that the decorator doesn't crash on immutable return types."""
    DecisionAuditor._is_warmed_up = False
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".anchor").mkdir()

    with patch("os.getcwd", return_value=str(project_dir)):
        @enforce()
        def mock_string_ai():
            return "This is a string."

        # Should NOT raise AttributeError
        result = mock_string_ai()
        assert result == "This is a string."
        # No _anchor_audit should be attached to a string
        assert not hasattr(result, "_anchor_audit")

def test_single_warmup_logic(tmp_path):
    """Verifies that exactly one warm-up occurs across all calls."""
    # Reset class state correctly
    DecisionAuditor._is_warmed_up = False
    DecisionAuditor._shared_engine = None
    DecisionAuditor._project_name = None
    DecisionAuditor._git_commit = None
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".anchor").mkdir()

    with patch("os.getcwd", return_value=str(project_dir)):
        # We patch the method on the CLASS before initializing the auditor
        with patch.object(DecisionAuditor, "_warm_up_cache") as mock_warmup:
            # Simulate the state change that the real warm-up does
            def side_effect():
                DecisionAuditor._is_warmed_up = True
            mock_warmup.side_effect = side_effect
            
            # Decorators themselves no longer trigger warm-up
            @enforce()
            def f1(): return MockResponse("res1")
            
            @enforce()
            def f2(): return MockResponse("res2")
            
            # First execution triggers warm-up
            f1()
            # Second execution skips it because _is_warmed_up is now True
            f2()
            
            # Verify called (exactly once)
            mock_warmup.assert_called_once()
