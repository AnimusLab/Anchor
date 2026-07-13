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


def test_engine_runtime_integration_check(tmp_path):
    # Setup standard rules requiring runtime interception
    config = {
        "rules": [
            {
                "id": "EU-ART12",
                "name": "Record Keeping",
                "severity": "blocker",
                "obligation_type": "provenance",
                "description": "Requires logs"
            },
            {
                "id": "SEC-001",
                "name": "Regular Static Rule",
                "severity": "error",
                "pattern": "some_static_pattern"
            }
        ]
    }
    engine = PolicyEngine(config)
    
    # Case A: Scans codebase with AI imports but NO anchor.runtime integration
    project_dir = tmp_path / "project_no_rt"
    project_dir.mkdir()
    # Write a file using openai but missing anchor.runtime
    (project_dir / "app.py").write_text("import openai\nclient = openai.OpenAI()")
    
    results = engine.scan_directory(str(project_dir))
    # It should detect openai import, see that anchor.runtime is missing, and trigger a violation for EU-ART12
    violations = results["violations"]
    assert len(violations) == 1
    assert violations[0]["id"] == "EU-ART12"
    assert "Runtime integration missing" in violations[0]["message"]
    
    # Case B: Scans codebase with AI imports AND anchor.runtime integrated
    project_dir_with_rt = tmp_path / "project_with_rt"
    project_dir_with_rt.mkdir()
    (project_dir_with_rt / "app.py").write_text("import anchor.runtime\nimport openai\nclient = openai.OpenAI()")
    
    results_with_rt = engine.scan_directory(str(project_dir_with_rt))
    # Integration check is satisfied, so no violations should be raised
    assert len(results_with_rt["violations"]) == 0

    # Case C: Scans codebase with NO AI imports (and no anchor.runtime)
    project_dir_no_ai = tmp_path / "project_no_ai"
    project_dir_no_ai.mkdir()
    (project_dir_no_ai / "app.py").write_text("print('hello world')")
    
    results_no_ai = engine.scan_directory(str(project_dir_no_ai))
    # No AI libraries are imported, so EU-ART12 should not trigger
    assert len(results_no_ai["violations"]) == 0

def test_generic_severity_floor_clamping():
    # Setup a dummy rule (TEST-999) with min_severity: "error"
    config = {
        "rules": [
            {
                "id": "TEST-999",
                "name": "Custom Command Execution",
                "pattern": "os.system\\(.*\\)",
                "severity": "blocker",
                "min_severity": "error",
                "message": "Dangerous command"
            }
        ]
    }
    engine = PolicyEngine(config)
    from anchor.adapters.python import PythonAdapter
    adapter = PythonAdapter()
    
    # Static call without AI influence (should downgrade, but not below min_severity = error)
    content = b"import os\nos.system('ls')\n"
    results = engine.scan_file(content, "test.py", adapter)
    
    assert len(results["violations"]) == 1
    assert results["violations"][0]["id"] == "TEST-999"
    # It would normally downgrade to "warning" if no floor existed, but since min_severity is "error", it must hold at "error"
    assert results["violations"][0]["severity"] == "error"

