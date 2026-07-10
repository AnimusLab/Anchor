import pytest
from anchor.core.engine import PolicyEngine
from anchor.adapters.python import PythonAdapter

def test_min_mitigations_not_satisfied():
    # File has the violation but NO mitigation comments
    content = b"""
def run_process():
    dangerous_call()
"""
    rules = [
        {
            "id": "SEC-007",
            "name": "Shell Command Execution",
            "match": {
                "type": "regex",
                "pattern": r"dangerous_call\("
            },
            "min_mitigations": 1,
            "message": "Shell command execution detected.",
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    
    results = engine.scan_file(content, "test.py", adapter)
    assert len(results["violations"]) == 1

def test_min_mitigations_satisfied_single():
    # File has the violation and ONE mitigation comment
    content = b"""
# anchor: mitigate SEC-007
def run_process():
    dangerous_call()
"""
    rules = [
        {
            "id": "SEC-007",
            "name": "Shell Command Execution",
            "match": {
                "type": "regex",
                "pattern": r"dangerous_call\("
            },
            "min_mitigations": 1,
            "message": "Shell command execution detected.",
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    
    results = engine.scan_file(content, "test.py", adapter)
    assert len(results["violations"]) == 0

def test_min_mitigations_multiple_required():
    # File has one mitigation comment but needs two
    content = b"""
# anchor: mitigate SEC-007
def run_process():
    dangerous_call()
"""
    rules = [
        {
            "id": "SEC-007",
            "name": "Shell Command Execution",
            "match": {
                "type": "regex",
                "pattern": r"dangerous_call\("
            },
            "min_mitigations": 2,
            "message": "Shell command execution detected.",
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    
    results = engine.scan_file(content, "test.py", adapter)
    assert len(results["violations"]) == 1

    # Now add a second mitigation comment and verify it passes
    content_two = b"""
# anchor: mitigate SEC-007
# anchor: mitigation SEC-007: Checked arguments
def run_process():
    dangerous_call()
"""
    results_two = engine.scan_file(content_two, "test.py", adapter)
    assert len(results_two["violations"]) == 0

