"""
Anchor Governance Analyst — Compliance Report Generator
Formats raw Rust engine scan results and statutory mappings into JSON, Markdown, and terminal reports.
"""

import json
from typing import Dict, Any, List

class GovernanceReportGenerator:
    """
    Renders compliance reports with statutory mappings, risk density scores,
    and remediation recommendations.
    """
    
    @staticmethod
    def render_markdown(audit_report: Dict[str, Any], statutory_mappings: List[Dict[str, Any]]) -> str:
        status_badge = "✅ COMPLIANT" if audit_report.get("is_compliant") else "🚨 VIOLATION BREACH"
        risk_score = audit_report.get("risk_score", 0.0)
        risk_level = audit_report.get("risk_level", "LOW")
        latency = audit_report.get("execution_microsec", 0)
        version = audit_report.get("rule_version", "6.0.0")

        md = []
        md.append(f"# 🛡️ Anchor Governance Compliance Report")
        md.append(f"**Status**: {status_badge} | **Systemic Risk Score**: `{risk_score}/10.0` ({risk_level})")
        md.append(f"**Engine**: `Anchor Core v{version}` | **Scan Latency**: `{latency} µs`\n")
        md.append("---")

        violations = audit_report.get("violations", [])
        if not violations:
            md.append("\n### ✅ No Governance Invariant Breaches Detected.")
            md.append("All AST nodes, system prompts, and tool interfaces passed statutory rules.")
        else:
            md.append(f"\n### 🚨 Detected Violations ({len(violations)})")
            for idx, v in enumerate(violations, 1):
                md.append(f"{idx}. `{v}`")

        if statutory_mappings:
            md.append("\n### 🏛️ Statutory Regulatory Mappings")
            md.append("| Rule ID | Framework / Regulation | Article / Requirement | Jurisdiction | Penalty Severity |")
            md.append("|---|---|---|---|---|")
            for m in statutory_mappings:
                md.append(
                    f"| `{m['rule_id']}` | **{m['statute_title']}** | {m['primary_article']} | {m['jurisdiction']} | `{m['penalty_level']}` |"
                )

        md.append("\n---")
        md.append("*Report generated automatically by AnimusLab Anchor Core (Rust Engine).*")
        return "\n".join(md)

    @staticmethod
    def render_json(audit_report: Dict[str, Any], statutory_mappings: List[Dict[str, Any]]) -> str:
        payload = {
            "report_meta": {
                "engine": "Anchor Core Rust Kernel",
                "version": audit_report.get("rule_version"),
                "scan_latency_us": audit_report.get("execution_microsec")
            },
            "assessment": {
                "is_compliant": audit_report.get("is_compliant"),
                "risk_score": audit_report.get("risk_score"),
                "risk_level": audit_report.get("risk_level")
            },
            "violations": audit_report.get("violations", []),
            "statutory_mappings": statutory_mappings
        }
        return json.dumps(payload, indent=2)
