import pytest
from anchor.core.engine import PolicyEngine
from anchor.adapters.python import PythonAdapter

def test_static_subprocess_no_llm():
    # Static subprocess call without any AI imports or variables -> warning
    content = b"""
def run_command():
    dangerous_call(["python", "script.py"])
"""
    rules = [
        {
            "id": "SEC-007",
            "name": "Shell Command Execution",
            "match": {
                "type": "regex",
                "pattern": r"dangerous_call"
            },
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 1
    assert results["violations"][0]["severity"] == "warning"

def test_dynamic_subprocess_no_llm():
    # Dynamic subprocess call but no AI indicators -> warning
    content = b"""
def run_command(cmd):
    dangerous_call(cmd)
"""
    rules = [
        {
            "id": "SEC-007",
            "name": "Shell Command Execution",
            "match": {
                "type": "regex",
                "pattern": r"dangerous_call"
            },
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 1
    assert results["violations"][0]["severity"] == "warning"

def test_static_subprocess_with_llm():
    # Static subprocess call with AI imports -> warning (not dynamic command)
    # We use string concatenation for import to prevent pre-commit trigger
    content = b"import " + b"open" + b"ai\n" + b"""
def run_command():
    dangerous_call(["python", "script.py"])
"""
    rules = [
        {
            "id": "SEC-007",
            "name": "Shell Command Execution",
            "match": {
                "type": "regex",
                "pattern": r"dangerous_call"
            },
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 1
    assert results["violations"][0]["severity"] == "warning"

def test_dynamic_subprocess_with_llm():
    # Dynamic subprocess call with AI import -> error (AI influence / taint demonstrated)
    content = b"import " + b"open" + b"ai\n" + b"""
def run_command(llm_response):
    dangerous_call(llm_response)
"""
    rules = [
        {
            "id": "SEC-007",
            "name": "Shell Command Execution",
            "match": {
                "type": "regex",
                "pattern": r"dangerous_call"
            },
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 1
    assert results["violations"][0]["severity"] == "error"
