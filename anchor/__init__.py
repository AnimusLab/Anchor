"""
Anchor - Deterministic Intent Auditor

Verify that code still means what it was supposed to mean.

Usage:
    from anchor import RepositoryAnalyzer
    
    analyzer = RepositoryAnalyzer('/path/to/repo')
    result = analyzer.audit_symbol('path/to/file.py', 'function_name')
    print(result.verdict)  # aligned | semantic_overload | intent_violation | dependency_inertia

CLI Usage:
    anchor audit path/to/file.py::function_name
    anchor batch symbols.txt
    anchor validate
"""

__version__ = "0.1.0"

from .symbols import (
    Symbol,
    IntentAnchor,
    CallContext,
    Role,
    Metrics,
    AuditResult,
    Verdict,
    Confidence,
)

from .repo import RepositoryAnalyzer
from .history import HistoryAnalyzer
from .contexts import ContextExtractor, RoleClusterer
from .verdicts import DriftDetector
from .report import ReportFormatter

__all__ = [
    # Core types
    "Symbol",
    "IntentAnchor",
    "CallContext",
    "Role",
    "Metrics",
    "AuditResult",
    "Verdict",
    "Confidence",

    # Main API
    "RepositoryAnalyzer",

    # Components (for advanced usage)
    "HistoryAnalyzer",
    "ContextExtractor",
    "RoleClusterer",
    "DriftDetector",
    "ReportFormatter",
]
