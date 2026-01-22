"""Core data models for Anchor."""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime


@dataclass
class IntentAnchor:
    """Frozen intent baseline from first meaningful commit."""

    commit_sha: str
    commit_date: datetime
    commit_message: str
    docstring: Optional[str]
    source: str
    lines_of_code: int
    confidence: Literal["high", "medium", "low"] = "high"

    def __repr__(self) -> str:
        return f"IntentAnchor({self.commit_sha[:8]}, {self.commit_date.date()})"


@dataclass
class CallContext:
    """A single call site with surrounding context."""

    caller_module: str
    caller_function: str
    surrounding_code: str
    line_number: int
    file_path: str

    def __repr__(self) -> str:
        return f"CallContext({self.caller_module}::{self.caller_function}, L{self.line_number})"


@dataclass
class Role:
    """A semantic role (cluster of related call contexts)."""

    contexts: List[CallContext]
    percentage: float
    description: str = ""
    embedding_centroid: Optional[List[float]] = None

    def __repr__(self) -> str:
        return f"Role({len(self.contexts)} contexts, {self.percentage:.1%})"


@dataclass
class Symbol:
    """A symbol being audited for intent drift."""

    name: str
    type: Literal["function", "class", "method"]
    file_path: str
    repo_path: str
    intent_anchor: IntentAnchor
    call_contexts: List[CallContext] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Symbol({self.name}, {self.type}, {len(self.call_contexts)} calls)"


@dataclass
class Metrics:
    """Calculated metrics for drift detection."""

    # Role-based metrics
    role_count: int
    role_percentages: List[float]
    max_role_percentage: float
    pairwise_role_similarity: List[float]

    # Intent alignment
    intent_alignment_percentage: float
    original_intent_role_percentage: float
    primary_role_is_original: bool

    # Evolution metrics
    violated_assumptions_count: int
    changes_in_5_years: int
    git_history_depth: int

    # Features
    unused_original_features_percentage: float

    # Workarounds and alternatives
    workaround_percentage: float
    has_documented_alternatives: bool
    dependent_count: int

    # Confidence factors
    call_site_count: int
    intent_anchor_confidence: Literal["high", "medium", "low"]
    clustering_quality: float

    def __repr__(self) -> str:
        return f"Metrics({self.role_count} roles, {self.intent_alignment_percentage:.1%} aligned)"


Verdict = Literal[
    "aligned",
    "semantic_overload",
    "intent_violation",
    "dependency_inertia",
    "confidence_too_low"
]

Confidence = Literal["high", "medium", "low"]


@dataclass
class AuditResult:
    """Complete audit result for a symbol."""

    symbol: Symbol
    roles: List[Role]
    metrics: Metrics
    verdict: Verdict
    confidence: Confidence
    evidence: dict

    def __repr__(self) -> str:
        return f"AuditResult({self.symbol.name}: {self.verdict}, {self.confidence})"
