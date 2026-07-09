import pytest
from anchor.core.engine import PolicyEngine
from anchor.adapters.python import PythonAdapter

def test_aln_001_without_validation():
    # LLM API call without any validation markers
    content = b"""
import os

def call_model():
    client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
"""
    rules = [
        {
            "id": "MIT-003-A",
            "rule_id": "ALN-001",
            "name": "LLM Output Without Validation",
            "match": {
                "type": "regex",
                "pattern": r"\.(create|send)\s*\("
            },
            "message": "LLM API call detected. Ensure output is validated.",
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    
    results = engine.scan_file(content, "test.py", adapter)
    assert len(results["violations"]) == 1
    assert "MIT-003-A" in results["violations"][0]["id"]

def test_aln_001_with_validation_pydantic():
    # LLM API call accompanied by pydantic import
    content = b"""
import os
from pydantic import BaseModel

class OutputSchema(BaseModel):
    response: str

def call_model():
    client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
"""
    rules = [
        {
            "id": "MIT-003-A",
            "rule_id": "ALN-001",
            "name": "LLM Output Without Validation",
            "match": {
                "type": "regex",
                "pattern": r"\.(create|send)\s*\("
            },
            "message": "LLM API call detected. Ensure output is validated.",
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    
    results = engine.scan_file(content, "test.py", adapter)
    # The evaluation pipeline should discard this candidate because of BaseModel/pydantic
    assert len(results["violations"]) == 0

def test_aln_001_with_validation_comment():
    # LLM API call with explicit validation comment
    content = b"""
def call_model():
    # anchor: validate
    client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
"""
    rules = [
        {
            "id": "MIT-003-A",
            "rule_id": "ALN-001",
            "name": "LLM Output Without Validation",
            "match": {
                "type": "regex",
                "pattern": r"\.(create|send)\s*\("
            },
            "message": "LLM API call detected. Ensure output is validated.",
            "severity": "error"
        }
    ]
    engine = PolicyEngine(config={"rules": rules})
    adapter = PythonAdapter()
    
    results = engine.scan_file(content, "test.py", adapter)
    assert len(results["violations"]) == 0
