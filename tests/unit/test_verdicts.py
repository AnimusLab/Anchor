import pytest
from datetime import datetime
from anchor.core.models import IntentAnchor, CallContext, VerdictType
from anchor.core.verdicts import analyze_drift

def test_analyze_drift_aligned():
    anchor = IntentAnchor(
        symbol="MyWidget",
        commit_sha="abc123",
        commit_date=datetime(2023, 1, 1),
        intent_description="A widget for rendering HTML forms.",
        original_assumptions=[]
    )
    # Correct usage (HTML methods)
    contexts = [
        CallContext(file_path="myapp/forms.py", line_number=10, caller_symbol="main", 
                    code_snippet="w.render()", uses_html_methods=True),
        CallContext(file_path="myapp/views.py", line_number=20, caller_symbol="view", 
                    code_snippet="w.as_p()", uses_html_methods=True),
        CallContext(file_path="myapp/utils.py", line_number=30, caller_symbol="helper", 
                    code_snippet="w.render()", uses_html_methods=True),
        CallContext(file_path="myapp/api.py", line_number=40, caller_symbol="api", 
                    code_snippet="w.render()", uses_html_methods=True)
    ]
    
    result = analyze_drift("MyWidget", anchor, contexts)
    assert result.verdict == VerdictType.ALIGNED
    assert "consistent" in result.rationale.lower() or "aligns" in result.rationale.lower()

def test_analyze_drift_intent_violation():
    anchor = IntentAnchor(
        symbol="MyWidget",
        commit_sha="abc123",
        commit_date=datetime(2023, 1, 1),
        intent_description="A widget for rendering HTML forms.",
        original_assumptions=[]
    )
    # Incorrect usage (no HTML methods, used as raw data holder in APIs)
    contexts = [
        CallContext(file_path="api/v1.py", line_number=10, caller_symbol="api", 
                    code_snippet="data = w.data", uses_html_methods=False),
        CallContext(file_path="api/v2.py", line_number=20, caller_symbol="api", 
                    code_snippet="val = w.value", uses_html_methods=False),
        CallContext(file_path="api/v3.py", line_number=30, caller_symbol="api", 
                    code_snippet="x = w.x", uses_html_methods=False),
        CallContext(file_path="myapp/forms.py", line_number=40, caller_symbol="main", 
                    code_snippet="w.render()", uses_html_methods=True)
    ]
    
    result = analyze_drift("MyWidget", anchor, contexts)
    # 3/4 = 75% violation, threshold is 60%
    assert result.verdict == VerdictType.INTENT_VIOLATION
    assert "remediation" in str(result).lower() or result.remediation is not None

def test_analyze_drift_semantic_overload():
    anchor = IntentAnchor(
        symbol="SharedUtils",
        commit_sha="xyz789",
        commit_date=datetime(2022, 5, 5),
        intent_description="Core logic utilities.",
        original_assumptions=[]
    )
    # Usage spread across too many domains (3+) without a clear owner
    # _cluster_by_module uses first 2 path segments as domain
    contexts = [
        CallContext(file_path="module_a/sub/file.py", line_number=1, caller_symbol="a", code_snippet="u.call()"),
        CallContext(file_path="module_b/sub/file.py", line_number=1, caller_symbol="b", code_snippet="u.call()"),
        CallContext(file_path="module_c/sub/file.py", line_number=1, caller_symbol="c", code_snippet="u.call()"),
        CallContext(file_path="module_d/sub/file.py", line_number=1, caller_symbol="d", code_snippet="u.call()")
    ]
    
    result = analyze_drift("SharedUtils", anchor, contexts)
    # 4 domains, each 25% (less than 70% dominance)
    assert result.verdict == VerdictType.SEMANTIC_OVERLOAD

def test_analyze_drift_dependency_inertia():
    anchor = IntentAnchor(symbol="OldThing", commit_sha="123", commit_date=datetime(2021, 1, 1),
                          intent_description="Legacy helper.", original_assumptions=[])
    # Only 2 usages (< 3 threshold)
    contexts = [
        CallContext(file_path="a/b/c.py", line_number=1, caller_symbol="x", code_snippet="o.done()"),
        CallContext(file_path="x/y/z.py", line_number=1, caller_symbol="y", code_snippet="o.done()")
    ]
    result = analyze_drift("OldThing", anchor, contexts)
    assert result.verdict == VerdictType.DEPENDENCY_INERTIA
