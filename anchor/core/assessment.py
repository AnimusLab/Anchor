"""
Anchor Executive Summary & Root Governance Risk Assessment Engine
"""

from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class RiskCluster:
    title: str
    severity: str
    confidence: str
    evidence_strength: str
    recommended_priority: str
    why_flagged: str
    risk_narrative: str
    friction: str
    counterarguments: str
    remediation: str
    affected_components: List[str] = field(default_factory=list)

class ArchitecturalAssessmentEngine:
    @classmethod
    def assess_security_compliance(cls, violations: List[dict]) -> List[RiskCluster]:
        clusters = []
        if not violations:
            return clusters

        # 1. Unsandboxed Subprocess Execution (SEC-007 / ANC-018 / RI-12)
        sub_violations = [v for v in violations if "SEC-007" in v.get("id", "") or "ANC-018" in v.get("id", "") or "RI-12" in v.get("id", "")]
        if sub_violations:
            components = [f"{v.get('file', '')}:{v.get('line', '')}" for v in sub_violations]
            clusters.append(RiskCluster(
                title="Unsandboxed Agent Execution",
                severity="Critical",
                confidence="High",
                evidence_strength="Strong",
                recommended_priority="Immediate",
                why_flagged=f"Detected direct invocation of native system execution commands (like subprocess or os.system) in {len(components)} locations.",
                risk_narrative="Agent tools execute shell commands or launch subprocesses natively on the host system without sandboxed container boundaries.",
                friction="Security controls become bypassable, and host systems become vulnerable to command injection or unauthorized modifications during agent actions.",
                counterarguments="The agent execution environment itself might be hosted inside a secure, short-lived Docker container or micro-vm, rendering additional sandbox wrappers redundant.",
                remediation="Route subprocess calls through the Diamond Cage WASM sandbox or wrap in sandboxed subprocess handlers.",
                affected_components=components
            ))

        # 2. Runtime Governance Missing
        has_runtime = any("anchor.runtime" in v.get("file", "") for v in violations)
        if not has_runtime:
            clusters.append(RiskCluster(
                title="Runtime Governance Missing",
                severity="Critical",
                confidence="Medium",
                evidence_strength="Moderate",
                recommended_priority="Immediate",
                why_flagged="No active imports of 'anchor.runtime' or '@anchor.enforce' decorators were detected in the application, but AI libraries are present.",
                risk_narrative="The application does not initialize the runtime compliance engine, leaving active policies in constitution.anchor unenforced.",
                friction="Governance decisions become difficult to verify, and future audits become harder to pass due to lack of explainability, human oversight, and data retention enforcement.",
                counterarguments="The repository might be a CLI utility, an offline training pipeline, or may not execute LLM calls in a live production environment.",
                remediation="Import anchor.runtime at service entrypoints and enable Diamond Cage behavioral enforcement.",
                affected_components=["constitution.anchor:1"]
            ))

        # 3. Security Compliance Gap (SEC)
        sec_violations = [v for v in violations if v.get("id", "").startswith("SEC") or v.get("id", "").startswith("ANC-002")]
        if sec_violations:
            components = [f"{v.get('file', '')}:{v.get('line', '')}" for v in sec_violations]
            clusters.append(RiskCluster(
                title="Security Compliance Gap (SEC)",
                severity="Critical",
                confidence="High",
                evidence_strength="Strong",
                recommended_priority="Immediate",
                why_flagged=f"Encountered {len(sec_violations)} active violation(s) under category SEC.",
                risk_narrative="System violates active security and compliance statutes related to category SEC: Malicious or corrupted data is introduced into the training, fine-tuning, or retrieval pipeline, causing the model to learn incorrect behaviors, biased outputs, or backdoor triggers that activate under specific conditions.",
                friction="Future compliance audits become harder to satisfy, increasing regulatory exposure.",
                counterarguments="These rules may have been configured with high sensitivity thresholds or may be non-blocking in development environments.",
                remediation="Encrypt embeddings before vector store write; remove plain-text API secrets.",
                affected_components=components
            ))

        # 4. Alignment Compliance Gap (ALN)
        aln_violations = [v for v in violations if v.get("id", "").startswith("ALN") or v.get("id", "").startswith("ANC-003")]
        if aln_violations:
            components = [f"{v.get('file', '')}:{v.get('line', '')}" for v in aln_violations]
            clusters.append(RiskCluster(
                title="Security Compliance Gap (ALN)",
                severity="Moderate",
                confidence="Medium",
                evidence_strength="Moderate",
                recommended_priority="Near-Term",
                why_flagged=f"Encountered {len(aln_violations)} active violation(s) under category ALN.",
                risk_narrative="System violates active security and compliance statutes related to category ALN: AI models generate factually incorrect or non-existent information.",
                friction="Future compliance audits become harder to satisfy, increasing regulatory exposure.",
                counterarguments="These rules may have been configured with high sensitivity thresholds or may be non-blocking in development environments.",
                remediation="Add system prompt guardrails and validation layers before output ingestion.",
                affected_components=components
            ))

        return clusters

def generate_executive_summary_text(clusters: List[RiskCluster]) -> str:
    if not clusters:
        return ""
    lines = []
    lines.append("=" * 70)
    lines.append("=== EXECUTIVE SUMMARY ===")
    lines.append("=" * 70)
    crit_count = sum(1 for c in clusters if c.severity.lower() == "critical")
    mod_count = sum(1 for c in clusters if c.severity.lower() == "moderate")
    lines.append(f"Root Governance Risks: {len(clusters)}")
    lines.append(f"  Critical:  {crit_count}")
    lines.append(f"  Moderate:  {mod_count}")
    lines.append("-" * 70)

    for i, c in enumerate(clusters, 1):
        lines.append(f"ROOT GOVERNANCE RISK #{i}")
        lines.append(f"  Title:             {c.title}")
        lines.append(f"  Severity:          {c.severity}")
        lines.append(f"  Confidence:        {c.confidence}")
        lines.append(f"  Evidence Strength: {c.evidence_strength}")
        lines.append(f"  Priority:          {c.recommended_priority}")
        lines.append(f"  Why Flagged:       {c.why_flagged}")
        lines.append(f"  Narrative:         {c.risk_narrative}")
        lines.append(f"  Friction:          {c.friction}")
        lines.append(f"  Counterarguments:  {c.counterarguments}")
        lines.append(f"  Remedy:            {c.remediation}")
        lines.append("  Evidence:")
        for comp in c.affected_components[:5]:
            lines.append(f"    · {comp}")
        if len(c.affected_components) > 5:
            lines.append(f"    · ... and {len(c.affected_components) - 5} more components.")
        lines.append("-" * 70)

    lines.append("\n")
    return "\n".join(lines)
