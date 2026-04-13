import pytest
from anchor.core.engine import PolicyEngine
from anchor.adapters.python import PythonAdapter

def test_engine_regex_match():
    # Setup a dummy rule with regex pattern
    config = {
        "rules": [
            {
                "id": "SEC-001",
                "name": "Hardcoded Secret",
                "pattern": "secret_key = \"[A-Za-z0-9]{16,}\"",
                "severity": "error",
                "message": "Do not hardcode secrets"
            }
        ]
    }
    engine = PolicyEngine(config)
    adapter = PythonAdapter()
    
    content = b"import os\nsecret_key = \"abc123def456ghi7\"\nprint('done')"
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 1
    assert results["violations"][0]["id"] == "SEC-001"
    assert results["violations"][0]["line"] == 2

def test_engine_ast_match_function_call():
    # Setup a dummy rule with AST match for eval()
    config = {
        "rules": [
            {
                "id": "SEC-002",
                "name": "Dangerous Eval",
                "match": {
                    "type": "function_call",
                    "name": "eval"
                },
                "severity": "blocker",
                "message": "Use of eval() is strictly prohibited"
            }
        ]
    }
    engine = PolicyEngine(config)
    adapter = PythonAdapter()
    
    content = b"user_input = '__import__(\"os\").system(\"ls\")'\neval(user_input)"
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 1
    assert results["violations"][0]["id"] == "SEC-002"
    assert results["violations"][0]["line"] == 2

def test_engine_suppression():
    # Use a simple name like 'exec' for basic identifier match test
    config = {
        "rules": [
            {
                "id": "SEC-003",
                "name": "Dangerous Exec",
                "match": {
                    "type": "function_call",
                    "name": "exec"
                },
                "severity": "error"
            }
        ]
    }
    engine = PolicyEngine(config)
    adapter = PythonAdapter()
    
    # Suppressed line - Rule ID must match exactly for suppression to work
    content = b"code = 'print(1)'\nexec(code) # anchor: ignore SEC-003"
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 0
    # Note: suppression detection depends on regex match or AST match
    # For function_call, it should find it.
    assert len(results["suppressed"]) == 1
    assert "SEC-003" in results["suppressed"][0]["id"]

def test_engine_exclude_path():
    config = {
        "exclude": ["tests/*", "vendor/**"]
    }
    engine = PolicyEngine(config)
    
    assert engine._is_path_excluded("tests/test_api.py", engine.config["exclude"]) == True
    assert engine._is_path_excluded("vendor/library/src.py", engine.config["exclude"]) == True
    assert engine._is_path_excluded("src/main.py", engine.config["exclude"]) == False
