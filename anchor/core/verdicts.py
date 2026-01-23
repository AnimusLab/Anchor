from typing import List
from anchor.core.models import AuditResult, IntentAnchor, CallContext, VerdictType, SemanticRole

def analyze_drift(symbol_name: str, anchor: IntentAnchor, contexts: List[CallContext]) -> AuditResult:
    """
    The Rule Engine. Applies invariant rules to determined verdict.
    """
    total_usages = len(contexts)
    if total_usages == 0:
        return AuditResult(
            symbol=symbol_name,
            anchor=anchor,
            observed_roles=[],
            verdict=VerdictType.CONFIDENCE_TOO_LOW,
            rationale="No usages found in codebase.",
            evidence=[]
        )

    # 1. Aggregate Roles
    html_rendering_count = sum(1 for c in contexts if c.uses_html_methods)
    validation_only_count = total_usages - html_rendering_count
    
    html_ratio = html_rendering_count / total_usages
    api_ratio = validation_only_count / total_usages

    roles = [
        SemanticRole(
            name="HTML Rendering", 
            description="Uses as_p(), as_table()", 
            call_count=html_rendering_count,
            usage_percentage=html_ratio,
            compatible_with_intent=True
        ),
        SemanticRole(
            name="Data Validation (No HTML)", 
            description="Only uses cleaning/validation", 
            call_count=validation_only_count,
            usage_percentage=api_ratio,
            compatible_with_intent=False # Based on Form's specific anchor
        )
    ]

    # 2. Apply Invariants (Hardcoded for Form v1)
    # Rule: Intent Violation if new role > 60% and original < 30%
    
    verdict = VerdictType.ALIGNED
    rationale = "Usage matches original intent."
    
    # Specific logic for Form (Intent Violation Detection)
    if "Form" in symbol_name:
        if api_ratio > 0.60:
            verdict = VerdictType.INTENT_VIOLATION
            rationale = (
                f"Primary usage ({api_ratio:.1%}) is Data Validation, which ignores "
                "the anchored HTML rendering capability. Original intent displaced."
            )
        elif api_ratio > 0.20:
            verdict = VerdictType.SEMANTIC_OVERLOAD
            rationale = "Significant split between HTML rendering and pure validation."

    return AuditResult(
        symbol=symbol_name,
        anchor=anchor,
        observed_roles=roles,
        verdict=verdict,
        rationale=rationale,
        evidence=[
            f"Total Usages: {total_usages}",
            f"HTML Usage: {html_ratio:.1%}",
            f"Validation Usage: {api_ratio:.1%}"
        ]
    )
    