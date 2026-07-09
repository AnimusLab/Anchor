from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class RiskCluster:
    title: str
    severity: str
    confidence: str
    recommended_priority: str
    risk_narrative: str
    business_impact: str
    remediation: str
    affected_components: List[str] = field(default_factory=list)

class RiskPattern:
    def __init__(self, pattern_id: str, title: str, severity: str,
                 recommended_priority: str, risk_narrative: str,
                 business_impact: str, remediation: str,
                 rule_ids: List[str] = None, message_keywords: List[str] = None):
        self.pattern_id = pattern_id
        self.title = title
        self.severity = severity
        self.recommended_priority = recommended_priority
        self.risk_narrative = risk_narrative
        self.business_impact = business_impact
        self.remediation = remediation
        self.rule_ids = rule_ids or []
        self.message_keywords = message_keywords or []

    def matches(self, violation: dict) -> bool:
        vid = violation.get('id', '')
        msg = violation.get('message', '').lower()
        if any(r in vid for r in self.rule_ids):
            return True
        if any(k in msg for k in self.message_keywords):
            return True
        return False

class ArchitecturalAssessmentEngine:
    @classmethod
    def assess_security_compliance(cls, violations: List[dict]) -> List[RiskCluster]:
        clusters = []
        if violations:
            clusters.append(RiskCluster(
                title="Security Compliance Gap",
                severity="Critical",
                confidence="High",
                recommended_priority="Immediate",
                risk_narrative="Compliance checks detected potential security gaps.",
                business_impact="Governance status and audit compliance are degraded.",
                remediation="Review findings and address identified vulnerabilities.",
                affected_components=[f"{v.get('file', '')}:{v.get('line', '')}" for v in violations]
            ))
        return clusters

    @classmethod
    def assess_architectural_drift(cls, results: List[Any], gov_map: dict) -> List[RiskCluster]:
        clusters = []
        if results:
            clusters.append(RiskCluster(
                title="Execution Governance Drift",
                severity="Moderate",
                confidence="Medium",
                recommended_priority="Near-Term",
                risk_narrative="Architectural drift checks detected inconsistencies.",
                business_impact="Maintainability and architectural integrity are degraded.",
                remediation="Review drift findings and align symbol usages.",
                affected_components=[getattr(r, 'file_path', '') for r in results if r]
            ))
        return clusters

def generate_executive_summary_text(clusters: List[RiskCluster]) -> str:
    if not clusters:
        return ""
    lines = ["=== EXECUTIVE SUMMARY ==="]
    for c in clusters:
        lines.append(f"\n[{c.severity}] {c.title}")
        lines.append(f"  Priority:   {c.recommended_priority} (Confidence: {c.confidence})")
        lines.append(f"  Impact:     {c.business_impact}")
        lines.append(f"  Narrative:  {c.risk_narrative}")
        lines.append(f"  Remediation: {c.remediation}")
        if c.affected_components:
            lines.append("  Affected Components:")
            for comp in c.affected_components[:5]:
                lines.append(f"    - {comp}")
            if len(c.affected_components) > 5:
                lines.append("    - ...")
    return "\n".join(lines)

def generate_executive_summary_markdown(clusters: List[RiskCluster]) -> str:
    if not clusters:
        return ""
    lines = ["# Executive Summary", ""]
    lines.append("| Risk Title | Severity | Priority | Confidence |")
    lines.append("| --- | --- | --- | --- |")
    for c in clusters:
        lines.append(f"| {c.title} | {c.severity} | {c.recommended_priority} | {c.confidence} |")
    lines.append("")
    for c in clusters:
        lines.append(f"## {c.title} ({c.severity})")
        lines.append(f"- **Confidence:** {c.confidence}")
        lines.append(f"- **Recommended Priority:** {c.recommended_priority}")
        lines.append(f"- **Business Impact:** {c.business_impact}")
        lines.append(f"- **Risk Narrative:** {c.risk_narrative}")
        lines.append(f"- **Remediation:** {c.remediation}")
        if c.affected_components:
            lines.append("- **Affected Components:**")
            for comp in c.affected_components:
                lines.append(f"  - {comp}")
        lines.append("")
    return "\n".join(lines)