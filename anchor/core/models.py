from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class VerdictType(Enum):
    ALIGNED = "aligned"
    SEMANTIC_OVERLOAD = "semantic_overload"
    INTENT_VIOLATION = "intent_violation"
    DEPENDENCY_INERTIA = "dependency_inertia"
    COMPLEXITY_DRIFT = "complexity_drift"
    CONFIDENCE_TOO_LOW = "confidence_too_low"


class AnchorConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CodeSymbol:
    """A raw symbol found in the codebase (before history analysis)."""
    name: str
    type: str  # 'class' or 'function' or 'method'
    file_path: str
    line_number: int
    parent: Optional[str] = None  # Name of the class if this is a method

    @property
    def qualified_name(self) -> str:
        """Approximates module path: django/forms/forms.py -> django.forms.forms.Form"""
        # Normalize path separators
        base = self.file_path.replace("\\", "/").replace("/", ".").replace(".py", "")
        # Remove leading dots if any
        base = base.lstrip(".")
        
        if self.parent:
            return f"{base}:{self.parent}.{self.name}"
        return f"{base}:{self.name}"

@dataclass
class IntentAnchor:
    """The frozen intent of a symbol at a specific point in time"""
    symbol: str
    commit_sha: str
    commit_date: datetime
    intent_description: str
    original_assumptions: List[str]
    source_code_snapshot: str = ""

    # Internal metadata
    confidence: AnchorConfidence = AnchorConfidence.LOW
    confidence_reason: str = "Inferred default"


@dataclass
class CallContext:
    """A specific usage instance of a symbol."""
    file_path: str
    line_number: int
    caller_symbol: str
    code_snippet: str

    # Analyzed properties (populated by analysis phase)
    uses_html_methods: bool = False
    uses_validation_only: bool = False
    is_async: bool = False
    

@dataclass
class SemanticRole:
    """A clustered group of call contexts representing a specific usage pattern."""
    name: str
    description: str
    call_count: int
    usage_percentage: float
    compatible_with_intent: bool  


@dataclass
class AuditResult:
    """The final deterministic judgment for a symbol."""
    symbol: str
    anchor: IntentAnchor
    observed_roles: List[SemanticRole]
    verdict: VerdictType
    rationale: str
    evidence: List[str]
    

def to_markdown(self) -> str:
    # We will implement the report generator later
    pass

    
    
