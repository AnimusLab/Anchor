import pytest
import os
from anchor.core.healer import suggest_fix, apply_fix, HealSuggestion

def test_suggest_fix_subprocess_shell(tmp_path):
    # Create a dummy file with a violation
    f = tmp_path / "unsafe.py"
    f.write_text("import subprocess\nsubprocess.run('ls', shell=True)\n", encoding="utf-8")
    
    violation = {
        "id": "SEC-007",
        "file": str(f),
        "line": 2,
        "message": "Shell injection risk"
    }
    
    suggestion = suggest_fix(violation)
    
    assert suggestion is not None
    assert "shell=False" in suggestion.suggested
    assert suggestion.auto_fixable == True

def test_suggest_fix_hardcoded_secret(tmp_path):
    f = tmp_path / "creds.py"
    f.write_text("api_key = \"definitely-a-secret-key-12345\"\n", encoding="utf-8")
    
    violation = {
        "id": "SEC-004",
        "file": str(f),
        "line": 1,
        "message": "Hardcoded secret"
    }
    
    suggestion = suggest_fix(violation)
    
    assert suggestion is not None
    assert "os.environ.get" in suggestion.suggested
    assert "API_KEY" in suggestion.suggested
    assert suggestion.auto_fixable == True

def test_apply_fix(tmp_path):
    f = tmp_path / "fixme.py"
    f.write_text("import os\nval = os.environ\n", encoding="utf-8")
    
    suggestion = HealSuggestion(
        rule_id="SEC-004",
        file=str(f),
        line=2,
        original="val = os.environ",
        suggested='val = os.environ.get("YOUR_KEY_NAME", "")',
        explanation="Targeted env access",
        auto_fixable=True
    )
    
    success = apply_fix(suggestion)
    assert success == True
    
    # Verify file content
    content = f.read_text(encoding="utf-8")
    assert 'val = os.environ.get("YOUR_KEY_NAME", "")' in content
    assert "import os" in content
