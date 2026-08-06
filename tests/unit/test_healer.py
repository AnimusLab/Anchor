import pytest
from anchor.core.healer import suggest_fix, format_suggestion_for_report

def test_suggest_fix_subprocess(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("result = subprocess.run(['ls'])")
    v = {"id": "SEC-007", "file": str(f), "line": 1, "message": "result = subprocess.run(['ls'])"}
    suggestion = suggest_fix(v)
    assert suggestion is not None
    assert suggestion.rule_id == "SEC-007"
    assert "subprocess" in suggestion.original
    formatted = format_suggestion_for_report(suggestion)
    assert "[✗]" in formatted


def test_suggest_fix_sec_002():
    v = {"id": "SEC-002", "file": "config.py", "line": 5, "message": 'api_key = "sk-1234567890123456"'}
    suggestion = suggest_fix(v)
    assert suggestion is not None
    assert suggestion.rule_id == "SEC-002"
    formatted = format_suggestion_for_report(suggestion)
    assert "Suggested Fix" in formatted

def test_suggest_fix_aln_001():
    v = {"id": "ALN-001", "file": "agent.py", "line": 100, "message": "client.chat.completions.create(model='gpt-4')"}
    suggestion = suggest_fix(v)
    assert suggestion is not None
    assert suggestion.rule_id == "ALN-001"

